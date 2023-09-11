"""Runner for starting blender or unreal as a rpc server."""

import os
import platform
import re
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from http.client import RemoteDisconnected
from pathlib import Path
from textwrap import dedent
from typing import Optional, Tuple
from xmlrpc.client import ProtocolError

from loguru import logger
from rich import get_console
from rich.prompt import Confirm

from .. import _tls
from ..data_structure.constants import EngineEnum, PathLike, plugin_name_blender, plugin_name_unreal, tmp_dir
from ..rpc import BLENDER_PORT, UNREAL_PORT, remote_blender, remote_unreal
from .downloader import download
from .setup import get_exec_path

# XXX: hardcode plugin download url
unreal_plugin_urls = dict(
    Windows={
        '5.1': 'https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/plugins/XRFeitoriaUnreal-0.5.0-UE5.1-Windows.zip',
        '5.2': 'https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/plugins/XRFeitoriaUnreal-0.5.0-UE5.2-Windows.zip',
    },
    Darwin={},
    Linux={},
)
blender_plugin_url = 'https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/plugins/XRFeitoriaBpy.zip'


def _rmtree(path: Path) -> None:
    """Remove tmp output."""
    if path.is_symlink():
        path.unlink()
    else:
        shutil.rmtree(path)


def _get_user_addon_path(version: str) -> Path:
    """Get user addon path depending on platform.

    Args:
        version (str): blender version, e.g. '3.3'

    Returns:
        Path: user addon path
    """
    user_path = Path.home()
    if platform.system() == 'Windows':
        user_addon_path = user_path / f'AppData/Roaming/Blender Foundation/Blender/{version}/scripts/addons'
    elif platform.system() == 'Linux':
        user_addon_path = user_path / f'.config/blender/{version}/scripts/addons'
    elif platform.system() == 'Darwin':
        user_addon_path = user_path / f'Library/Application Support/Blender/{version}/scripts/addons'
    return user_addon_path


class RPCRunner(ABC):
    """A wrapper for starting blender as a rpc server."""

    def __init__(
        self,
        new_process: bool = False,
        engine_exec: Optional[PathLike] = None,
        project_path: PathLike = '',
        replace_plugin: bool = False,
        dev_plugin: bool = False,
        background: bool = True,
    ) -> None:
        """Initialize RPCRunner.

        Args:
            new_process (bool, optional): whether to start a new process. Defaults to False.
            engine_exec (Optional[PathLike], optional): path to engine executable. Defaults to None.
            project_path (PathLike, optional): path to project. Defaults to ''.
            replace_plugin (bool, optional): whether to replace the plugin installed for the engine. Defaults to False.
            dev_plugin (bool, optional): Whether to use the plugin under local directory.
                If False, would use the plugin downloaded from a remote server. Defaults to False.
            background (bool, optional): whether to run the engine in background without GUI. Defaults to True.
        """
        self.console = get_console()
        self.engine_type: EngineEnum = _tls.cache.get('platform', None)
        self.engine_process: Optional[subprocess.Popen] = None
        self.new_process = new_process
        self.replace_plugin = replace_plugin
        self.dev_plugin = dev_plugin
        self.background = background
        self.debug = os.environ.get('RPC_DEBUG', '0') == '1'  # logger.level('DEBUG')

        if self.dev_plugin:
            self.replace_plugin = True
            logger.warning(
                '`dev_plugin=True` would force `replace_plugin=True`, replacing the plugin with local source code'
            )
        # Try to reuse existing engine process
        is_reuse = self.reuse()
        if is_reuse:
            return
        else:
            logger.debug('No existing engine process found, `new_process` is set to True to start a new process')
            self.new_process = True

        if not self.new_process and self.replace_plugin:
            logger.warning('`replace_plugin=True` will be ignored when `new_process=False`')
        # Initialize for new process
        if engine_exec:
            self.engine_exec = Path(engine_exec).resolve()
        else:
            self.engine_exec = get_exec_path(engine=self.engine_type)
        if not self.engine_exec.exists() or not self.engine_exec.is_file():
            raise FileExistsError(f'Engine executable not valid: {self.engine_exec}')
        logger.info(f'Using engine executable: "{self.engine_exec.as_posix()}"')
        self.project_path = Path(project_path).resolve() if project_path else None
        self.engine_info: Tuple[str, str] = self._get_engine_info(self.engine_exec)
        if self.engine_type == EngineEnum.unreal and (self.project_path is None or not self.project_path.exists()):
            raise FileExistsError(f'Project path not valid: "{self.project_path}"')

    @property
    def port(self) -> int:
        """Get RPC port depending on engine type."""
        if self.engine_type == EngineEnum.blender:
            return BLENDER_PORT
        elif self.engine_type == EngineEnum.unreal:
            return UNREAL_PORT
        else:
            raise NotImplementedError

    def __enter__(self) -> 'RPCRunner':
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

    # deprecated, use `with` instead
    # def __del__(self) -> None:
    #     if self.engine_process is not None:
    #         self.stop()

    def stop(self) -> None:
        """Stop rpc server."""
        import psutil

        process = self.engine_process
        if process is not None:
            logger.info(':bell: [bold red]Exiting RPC Server[/bold red], killing engine process')
            for child in psutil.Process(process.pid).children(recursive=True):
                if child.is_running():
                    logger.debug(f'Killing child process {child.pid}')
                    child.kill()
            process.kill()
            self.engine_process = None
        else:
            logger.info(':bell: [bold red]Exiting runner[/bold red], reused engine process remains')

    def reuse(self) -> bool:
        """Try to reuse existing engine process.

        Returns:
            bool: whether the engine process is reused.

        Raises:
            RuntimeError: if `new_process=True` but an existing engine process is found.
        """
        try:
            with self.console.status('[bold green]Try to reuse existing engine process...[/bold green]'):
                self.test_connection(debug=self.debug)
            logger.info(':direct_hit: [bold cyan]Reuse[/bold cyan] existing engine process')
            # raise an error if new_process is True
            if self.new_process:
                raise RuntimeError(
                    f'RPC server in `RPC_PORT={self.port}` already started! '
                    'This is raised when calling `init_blender` or `init_unreal` with `new_progress=True`'
                    'when an existing server (blender or unreal) is already running. \n'
                    '3 ways to get around this: \n'
                    '   - set `new_process=False` for using the existing server. \n'
                    '   - stop the server (engine process) and try again; \n'
                    "   - change the rpc port via system env 'RPC_PORT' and try again."
                )
        except ConnectionRefusedError:
            return False

        return True

    @staticmethod
    def _popen(cmd: str) -> subprocess.Popen:
        """Execute command.

        Args:
            cmd (str): command to execute.

        Returns:
            subprocess.Popen: process
        """
        logger.debug(f'Start engine, executing command:\n{cmd}')
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return process

    def start(self):
        """Start rpc server."""
        if not self.new_process:
            return

        with self.console.status('Initializing RPC server...') as status:
            status.update(status='[green bold]Installing plugin...')
            self._install_plugin()
            status.update(status=f'[green bold]Starting {" ".join(self.engine_info)} as RPC server...')
            self._start_rpc(background=self.background, project_path=self.project_path)
            _tls.cache['engine_process'] = self.engine_process
        logger.info(f'RPC server started at port {self.port}')

    def wait_for_start(self) -> None:
        """Wait 3 minutes for RPC server to start.

        After 3 minutes, ask user if they want to quit if it takes too long.
        """
        tryout_time = 180  # 3 minutes
        tryout_sec = 1
        tryout_num = tryout_time // tryout_sec

        _num = 0
        while True:
            try:
                self.test_connection(debug=self.debug)
                break
            except (RemoteDisconnected, ConnectionRefusedError, ProtocolError):
                logger.debug(f'Waiting for RPC server to start [tryout {_num}/{tryout_num}]')
                _num += 1
                time.sleep(tryout_sec)  # wait for 5 seconds
            if _num >= tryout_num:  # 3 minutes
                _quit = Confirm.ask(
                    f'{" ".join(self.engine_info)} loading seems to take a long time, do you want to quit?',
                    default=False,
                )
                if _quit:
                    self.stop()
                else:
                    _num = 0  # reset tryout times, wait for another 3 minutes

    @property
    @abstractmethod
    def src_plugin_path(self) -> Path:
        """Get plugin source path.

        priority:
            if `self.dev_plugin=False`: download from url > build from source

            if `self.dev_plugin=True`: build from source
        """
        pass

    @property
    def dst_plugin_dir(self) -> Path:
        """Get plugin directory."""
        if self.engine_type == EngineEnum.blender:
            dst_plugin_dir = _get_user_addon_path(version=self.engine_info[1]) / plugin_name_blender
        elif self.engine_type == EngineEnum.unreal:
            dst_plugin_dir = self.project_path.parent / 'Plugins' / plugin_name_unreal
        else:
            raise NotImplementedError
        dst_plugin_dir.parent.mkdir(exist_ok=True, parents=True)
        logger.debug(f'Installing plugin to "{dst_plugin_dir.as_posix()}"')
        return dst_plugin_dir

    ##########################
    # ----- abstracts ----- #
    ##########################

    @staticmethod
    @abstractmethod
    def _get_engine_info(engine_exec: Path) -> Tuple[str, str]:
        pass

    @abstractmethod
    def _get_cmd(self) -> str:
        pass

    @abstractmethod
    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = '') -> None:
        pass

    def _get_plugin_url(self) -> Optional[str]:
        if self.engine_type == EngineEnum.blender:
            return blender_plugin_url
        elif self.engine_type == EngineEnum.unreal:
            engine_version = self.engine_info[1]
            return unreal_plugin_urls[platform.system()].get(engine_version, None)
        else:
            raise NotImplementedError

    def _install_plugin(self) -> None:
        """Install plugin."""
        dst_plugin_dir = self.dst_plugin_dir
        # TODO: check version of dst_plugin_dir, if old, set self.replace_plugin = True
        # skip if plugin already exists
        if dst_plugin_dir.exists():
            if self.replace_plugin:
                if self.engine_type == EngineEnum.unreal:
                    logger.warning(f'Removing existing plugin {dst_plugin_dir}')
                    _rmtree(dst_plugin_dir)
                # skip deleting for blender
            else:
                logger.debug(f'Plugin {dst_plugin_dir} already exists')
                return

        src_plugin_path = self.src_plugin_path
        logger.info(f'Installing plugin from "{src_plugin_path.as_posix()}"')

        if self.engine_type == EngineEnum.blender:
            _script = f"""
                import bpy;
                bpy.ops.preferences.addon_install(filepath='{src_plugin_path.as_posix()}');
                bpy.ops.preferences.addon_enable(module='{plugin_name_blender}');
                bpy.context.preferences.view.show_splash = False;
                bpy.ops.wm.save_userpref()"""

            cmd = self._get_cmd(python_scripts=dedent(_script).replace('\n', ''))
            process = self._popen(cmd)
            process.wait()
        elif self.engine_type == EngineEnum.unreal:
            try:
                self.dst_plugin_dir.symlink_to(src_plugin_path, target_is_directory=True)
                logger.debug(f'Symlink {src_plugin_path} => {dst_plugin_dir}')
            except (OSError, PermissionError):
                logger.warning(
                    'Failed to create symlink: [u]permission denied[/u]. '
                    'Please consider running on [u]administrator[/u] mode. '
                    'Fallback to copy the plugin.'
                )
                shutil.copytree(src=src_plugin_path, dst=dst_plugin_dir)
                logger.debug(f'copy {src_plugin_path} => {dst_plugin_dir}')

        logger.info(f'Plugin installed in "{dst_plugin_dir}"')

    @staticmethod
    @abstractmethod
    def test_connection(debug: bool = False) -> None:
        pass


class BlenderRPCRunner(RPCRunner):
    @property
    def src_plugin_path(self) -> Path:
        """Get plugin source zip path."""
        if self.dev_plugin:
            from .publish_plugins import _make_archive

            src_plugin_dir = Path(__file__).resolve().parents[2] / 'src' / plugin_name_blender
            src_plugin_path = _make_archive(src_plugin_dir)
        else:
            url = self._get_plugin_url()
            if url:
                src_plugin_path = tmp_dir / Path(url).name  # with suffix (.zip)
                if src_plugin_path.exists() and not self.replace_plugin:
                    logger.debug(f'Downloaded Plugin {src_plugin_path} exists')
                    return src_plugin_path
                else:
                    src_plugin_path.unlink(missing_ok=True)

                try:
                    download(url=url, dst_dir=tmp_dir, verbose=False)
                except Exception:
                    raise RuntimeError(
                        f'Sorry, failed to download plugin from {url}\n'
                        'Try again later or set `init_blender(dev_plugin=True)` to build the plugin from source.\n'
                        'Clone the source code from https://github.com/openxrlab/xrfeitoria.git'
                    )
            else:
                # build plugin from source
                raise FileNotFoundError(
                    f'Sorry, pre-built plugin for {" ".join(self.engine_info)} in {platform.system()} not found!\n'
                    'Set `dev_plugin=True` in init_blender to build the plugin from source.\n'
                    'Clone the source code from https://github.com/openxrlab/xrfeitoria.git'
                )
        return src_plugin_path

    @staticmethod
    def _get_engine_info(blender_exec: Path) -> Tuple[str, str]:
        """Get blender version."""
        _version = None
        if platform.system() == 'Darwin':
            root_dir = blender_exec.parent.parent / 'Resources'
        else:
            root_dir = blender_exec.parent
        for file in root_dir.iterdir():
            if not file.is_dir():
                continue
            # e.g. 3.3, 2.93
            if re.match(r'\d+\.\d+', file.name):
                _version = file.name
                break

        if _version is None:
            raise FileNotFoundError(f'Cannot find blender executable in {blender_exec.parent}')

        return 'Blender', _version

    def _get_cmd(
        self,
        background: bool = True,
        project_path: Optional[Path] = '',
        python_scripts: Optional[str] = '',
    ) -> str:
        """Get blender command line.

        Args:
            background (bool, optional): Run blender in background without GUI. Defaults to True.
            project_path (Optional[Path], optional): Path to blender project. Defaults to ''.
            python_scripts (Optional[str], optional): Python scripts to run when blender starts. Defaults to ''.

        Returns:
            str: _description_
        """
        cmd = [
            f'"{self.engine_exec}"',
            '--background' if background else '',
            f'"{project_path}"' if project_path else '',
            f'--python-expr "{python_scripts}"' if python_scripts else '',
        ]
        return ' '.join(map(str, cmd))

    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = '') -> None:
        """Start rpc server.

        Args:
            background (bool, optional): Run blender in background without GUI. Defaults to True.
            project_path (Optional[Path], optional): Path to blender project. Defaults to ''.
        """
        # logger.info(f'Starting {" ".join(self.engine_info)} with RPC server at port {self.port}')

        # run server in blocking mode if background
        rpc_scripts = f'import bpy; bpy.ops.wm.start_rpc_servers(block={background}, port={self.port})'
        cmd = self._get_cmd(background=background, project_path=project_path, python_scripts=rpc_scripts)
        process = self._popen(cmd)

        self.wait_for_start()
        # logger.info(f'Started {" ".join(self.engine_info)} with RPC server at port {self.port}')
        self.engine_process = process

    @staticmethod
    @remote_blender(default_imports=[])
    def test_connection(debug: bool = False) -> bool:
        """Test connection."""
        try:
            from XRFeitoriaBpy import utils_logger

            level = 'DEBUG' if debug else 'INFO'
            _logger = utils_logger.setup_logger(level=level)
            _logger.debug('Connection test passed')
        except Exception:
            pass


class UnrealRPCRunner(RPCRunner):
    """UnrealRPCRunner."""

    @property
    def src_plugin_path(self) -> Path:
        """Get plugin source directory."""
        if self.dev_plugin:
            src_plugin_path = Path(__file__).resolve().parents[2] / 'src' / plugin_name_unreal
            if not src_plugin_path.exists():
                raise FileNotFoundError(
                    f'Plugin source code not found in {src_plugin_path}, '
                    'please set `dev_plugin=False` to download the pre-built plugin. '
                    'Or clone the source code and build the plugin from source. '
                    'https://github.com/openxrlab/xrfeitoria.git'
                )
        else:
            url = self._get_plugin_url()
            if url:
                src_plugin_root = tmp_dir / 'plugins'
                src_plugin_path = src_plugin_root / Path(url).stem  # remove suffix (.zip)
                if src_plugin_path.exists() and not self.replace_plugin:
                    logger.debug(f'Downloaded Plugin {src_plugin_path} exists')
                    return src_plugin_path
                else:
                    shutil.rmtree(src_plugin_root, ignore_errors=True)

                try:
                    plugin_compress = download(url=url, dst_dir=src_plugin_root, verbose=False)
                except Exception:
                    raise RuntimeError(
                        f'Sorry, failed to download plugin from {url}\n'
                        'Try again later or set `init_unreal(dev_plugin=True)` to build the plugin from source.\n'
                        'Clone the source code from https://github.com/openxrlab/xrfeitoria.git'
                    )
                shutil.unpack_archive(plugin_compress, src_plugin_root)
                assert src_plugin_path.exists(), f'Plugin download failed to {src_plugin_path}'
            else:
                # build plugin from source
                # TODO: add a instruction (link) to build the plugin
                raise FileNotFoundError(
                    f'Sorry, pre-built plugin for {" ".join(self.engine_info)} in {platform.system()} not found!\n'
                    'Set `dev_plugin=True` in init_unreal to build the plugin from source.\n'
                    'Clone the source code from https://github.com/openxrlab/xrfeitoria.git'
                )
        return src_plugin_path

    @staticmethod
    def _get_engine_info(unreal_exec: Path) -> Tuple[str, str]:
        """Get unreal version."""
        try:
            _version = re.findall(r'UE_(\d+\.\d+)', unreal_exec.as_posix())[0]
        except IndexError:
            raise FileNotFoundError(f'Cannot find unreal executable in {unreal_exec}')
        return 'Unreal', _version

    def _get_cmd(
        self,
        project_path: PathLike,
        background: bool = True,
        # python_scripts: Optional[str] = "",
        rpc_port: int = 9998,
    ) -> str:
        """Get unreal command line.

        Args:
            project_path (PathLike): Path to unreal project.
            background (bool, optional): Run unreal in background without GUI. Defaults to True.
            rpc_port (int, optional): RPC port. Defaults to 9998.

        Returns:
            str: _description_
        """
        assert not background, NotImplementedError('UnrealRPCRunner only support foreground mode for now')
        rpc_scripts = 'import unreal; bootstrap_unreal_with_rpc_server(block=True)'
        cmd = [
            f'"{self.engine_exec}"',
            f'"{project_path}"',
            f'-run=pythonscript -script="{rpc_scripts}"' if background else '',
            # f'-ExecutePythonScript="{python_script_path}"',
            # f'-ExecCmds="py {python_script_path}"',
            f'-rpc_port={rpc_port}',
            '-notexturestreaming',
            '-silent',
            'LOG=Pipeline.log',
            '-LOCALLOGTIMES',
        ]
        return ' '.join(map(str, cmd))

    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = '') -> None:
        """Start rpc server."""
        # logger.info(f'Starting {" ".join(self.engine_info)} with RPC server at port {self.port}')

        # run server in blocking mode if background
        cmd = self._get_cmd(
            background=background,
            project_path=project_path,
            rpc_port=self.port,
        )
        process = self._popen(cmd)

        self.wait_for_start()
        # logger.info(f'Started {" ".join(self.engine_info)} with RPC server at port {self.port}')
        self.engine_process = process

    @staticmethod
    @remote_unreal(default_imports=[])
    def test_connection(debug: bool = False) -> None:
        """Test connection."""
        import unreal

        unreal.log('Connection test passed')
