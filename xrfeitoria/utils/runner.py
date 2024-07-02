"""Runner for starting blender or unreal as a rpc server."""

import json
import os
import platform
import re
import shutil
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from bisect import bisect_left
from functools import lru_cache
from http.client import RemoteDisconnected
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Literal, Optional, Tuple, TypedDict
from urllib.error import HTTPError, URLError
from xmlrpc.client import ProtocolError

import psutil
from loguru import logger
from packaging.version import parse
from rich import get_console
from rich.prompt import Confirm

from .. import __version__, _tls
from ..data_structure.constants import (
    EngineEnum,
    PathLike,
    package_name,
    plugin_name_blender,
    plugin_name_pattern,
    plugin_name_unreal,
    tmp_dir,
)
from ..rpc import BLENDER_PORT, UNREAL_PORT, factory, remote_blender, remote_unreal
from .downloader import download
from .setup import get_exec_path

# XXX: hardcode download url
dist_root = os.environ.get('XRFEITORIA__DIST_ROOT') or 'https://github.com/openxrlab/xrfeitoria/releases/download'
plugin_infos_json = Path(__file__).parent.resolve() / 'plugin_infos.json'
plugin_info_type = TypedDict(
    'PluginInfo',
    {
        'plugin_name': str,
        'plugin_version': str,
        'engine_version': str,
        'platform': Literal['Windows', 'Linux', 'Darwin'],
    },
)


def _rmtree(path: Path) -> None:
    """Remove tmp output."""
    if path.is_symlink():
        path.unlink(missing_ok=True)
    elif path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


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
        reload_rpc_code: bool = False,
        replace_plugin: bool = False,
        dev_plugin: bool = False,
        background: bool = True,
    ) -> None:
        """Initialize RPCRunner.

        Args:
            new_process (bool, optional): whether to start a new process. Defaults to False.
            engine_exec (Optional[PathLike], optional): path to engine executable. Defaults to None.
            project_path (PathLike, optional): path to project. Defaults to ''.
            reload_rpc_code (bool, optional): whether to reload the registered rpc functions and classes.
                If you are developing the package or writing a custom remote function, set this to True to reload the code.
                This will only be in effect when `new_process=False` if the engine process is reused. Defaults to False.
            replace_plugin (bool, optional): whether to replace the plugin installed for the engine. Defaults to False.
            dev_plugin (bool, optional): Whether to use the plugin under local directory.
                If False, would use the plugin downloaded from a remote server. Defaults to False.
            background (bool, optional): whether to run the engine in background without GUI. Defaults to True.
        """
        self.console = get_console()
        self.engine_type: EngineEnum = _tls.cache.get('platform', None)
        self.engine_pid: Optional[int] = None
        self.engine_process: Optional[subprocess.Popen] = None
        self.engine_running: bool = False
        self.engine_outputs: List[str] = []
        self.new_process = new_process
        self.replace_plugin = replace_plugin
        self.dev_plugin = dev_plugin
        self.background = background
        self.debug = logger._core.min_level <= 10  # DEBUG level

        # child threads
        self.thread_engine_alive: Optional[threading.Thread] = None
        self.thread_receive_stdout: Optional[threading.Thread] = None

        if reload_rpc_code:
            # clear registered functions and classes for reloading
            factory.RPCFactory.registered_function_names.clear()
            factory.RPCFactory.reload_rpc_code = True

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
        if project_path:
            self.project_path = Path(project_path).resolve()
            assert self.project_path.exists(), (
                f'Project path is not valid: "{self.project_path.as_posix()}"\n'
                'Please check `xf.init_blender(project_path=...)` or `xf.init_unreal(project_path=...)`'
            )
            if self.engine_type == EngineEnum.blender:
                assert self.project_path.suffix == '.blend', (
                    f'Project path is not valid: "{self.project_path.as_posix()}"\n'
                    'Please use a blender project file (.blend) file as project path in `xf.init_blender(project_path=...)`'
                )
            elif self.engine_type == EngineEnum.unreal:
                assert self.project_path.suffix == '.uproject', (
                    f'Project path is not valid: "{self.project_path.as_posix()}"\n'
                    'Please use a unreal project file (.uproject) as project path in `xf.init_unreal(project_path=...)`'
                )
        else:
            assert (
                self.engine_type != EngineEnum.unreal
            ), 'Please specify a project path in `xf.init_unreal(project_path=...)` when using unreal engine'
            self.project_path = None
        self.engine_info: Tuple[str, str] = self._get_engine_info(self.engine_exec)

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
        # clear rpc server
        factory.RPCFactory.clear()

        # stop threads
        self.engine_running = False
        if self.thread_receive_stdout:
            self.thread_receive_stdout.join()
        if self.thread_engine_alive:
            self.thread_engine_alive.join()

        # stop engine process
        process = self.engine_process
        if process is not None:
            logger.info(':bell: [bold red]Exiting RPC Server[/bold red], killing engine process')
            if psutil.pid_exists(self.engine_pid):
                for child in psutil.Process(self.engine_pid).children(recursive=True):
                    if child.is_running():
                        logger.debug(f'Killing child process {child.pid}')
                        child.kill()
                process.kill()
            self.engine_process = None
            self.engine_pid = None
            # prevent to be called from another thread
            _tls.cache['engine_process'] = None
            _tls.cache['engine_pid'] = None
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
                self.engine_pid = self.get_pid()
            logger.info(':direct_hit: [bold cyan]Reuse[/bold cyan] existing engine process')
            # raise an error if new_process is True
            if self.new_process:
                raise RuntimeError(
                    f'RPC server in `RPC_PORT={self.port}` already started! '
                    'This is raised when calling `init_blender` or `init_unreal` with `new_progress=True`'
                    'if an existing server (blender or unreal) is already running. \n'
                    '3 ways to get around this: \n'
                    '   - Set `new_process=False` for using the existing server. \n'
                    '   - Stop the server (engine process) and try again; \n'
                    "   - Change the rpc port via system env 'RPC_PORT' and try again.\n"
                    'For multi-processing, please refer to https://xrfeitoria.readthedocs.io/en/latest/faq.html#rpc-port'
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

    def _receive_stdout(self) -> None:
        """Receive output from the subprocess, and log it in `trace` level.

        This function should be called in a separate thread.
        """
        # start receiving
        while True:
            try:
                data = self.engine_process.stdout.readline().decode()
            except AttributeError:
                break
            if not data:
                break
            # log in debug level
            logger.trace(f'(engine) {data.strip()}')
            self.engine_outputs.append(data)

    def check_engine_alive(self) -> None:
        """Check if the engine process is alive. This function should be called in a
        separate thread.

        Raises:
            RuntimeError: if engine process is not alive.
        """
        logger.debug('(Thread) Start checking engine process')
        while self.engine_running:
            if self.engine_process.poll() is not None:
                logger.error(self.get_process_output(self.engine_process))
                logger.error('[red]RPC server stopped unexpectedly, check the engine output above[/red]')
                self.engine_running = False  # for multi-processing
                factory.RPCFactory.clear()
                raise RuntimeError('RPC server stopped unexpectedly')
            time.sleep(5)

    def check_engine_alive_psutil(self) -> None:
        """Check if the engine process is alive using psutil. This function should be
        called in a separate thread.

        Raises:
            RuntimeError: if engine process is not alive.
        """
        logger.debug('(Thread) Start checking engine process, using psutil')
        p = psutil.Process(self.engine_pid)
        while self.engine_running:
            if not p.is_running():
                logger.error('[red]RPC server stopped unexpectedly[/red]')
                self.engine_running = False  # for multi-processing
                factory.RPCFactory.clear()
                raise RuntimeError('RPC server stopped unexpectedly')
            time.sleep(5)

    def get_process_output(self, process: subprocess.Popen) -> str:
        """Get process output when process is exited with non-zero code."""
        # engine_out = process.stdout.read().decode("utf-8")
        engine_out = ''.join(self.engine_outputs)
        out = (
            f'Engine process exited with code {process.poll()}\n\n'
            '[gray]>>>> Engine output >>>>\n\n[/gray]'
            f'{engine_out}\n'
            '[gray]<<<< Engine output <<<<\n[/gray]'
        )
        return out

    def start(self) -> None:
        """Start rpc server."""
        if not self.new_process:
            self.engine_running = True
            self.thread_engine_alive = threading.Thread(target=self.check_engine_alive_psutil, daemon=True).start()
            return

        with self.console.status('Initializing RPC server...') as status:
            status.update(status='[green bold]Installing plugin...')
            self._install_plugin()
            status.update(status=f'[green bold]Starting {" ".join(self.engine_info)} as RPC server...')
            self.engine_process = self._start_rpc(background=self.background, project_path=self.project_path)
            self.engine_running = True
            self.engine_pid = self.engine_process.pid
            _tls.cache['engine_process'] = self.engine_process
            _tls.cache['engine_pid'] = self.engine_pid
        logger.info(f'RPC server started at port {self.port}')

        # check if engine process is alive in a separate thread
        self.thread_receive_stdout = threading.Thread(target=self._receive_stdout, daemon=True).start()
        self.thread_engine_alive = threading.Thread(target=self.check_engine_alive, daemon=True).start()

    def wait_for_start(self, process: subprocess.Popen) -> None:
        """Wait 3 minutes for RPC server to start.

        After 3 minutes, ask user if they want to quit if it takes too long.

        Args:
            process (subprocess.Popen): process to wait for.
        """
        tryout_time = 180  # 3 minutes
        tryout_sec = 1
        tryout_num = tryout_time // tryout_sec

        _num = 0
        while True:
            if process.poll() is not None:
                error_msg = self.get_process_output(process)
                logger.error(error_msg)

                if 'Unable to open a display' in error_msg:
                    raise RuntimeError(
                        'Failed to start RPC server. Please run blender in background mode. '
                        'Set `background=True` in `init_blender`. '
                    )
                raise RuntimeError('RPC server failed to start. Check the engine output above.')
            try:
                self.test_connection(debug=self.debug)
                break
            except (RemoteDisconnected, ConnectionRefusedError, ProtocolError):
                logger.debug(f'Waiting for RPC server to start (tryout {_num}/{tryout_num})')
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

    @abstractmethod
    def get_src_plugin_path(self) -> Path:
        """Get plugin source path, including downloading or symlinking/copying from
        local directory.

        priority:
            if `self.dev_plugin=False`: download from url > build from source

            if `self.dev_plugin=True`: build from source

        Returns:
            Path: plugin source path
        """
        pass

    @property
    @lru_cache
    def dst_plugin_dir(self) -> Path:
        """Get plugin directory to install."""
        if self.engine_type == EngineEnum.blender:
            dst_plugin_dir = _get_user_addon_path(version=self.engine_info[1]) / plugin_name_blender
        elif self.engine_type == EngineEnum.unreal:
            dst_plugin_dir = self.project_path.parent / 'Plugins' / plugin_name_unreal
        else:
            raise NotImplementedError
        dst_plugin_dir.parent.mkdir(exist_ok=True, parents=True)
        return dst_plugin_dir

    @property
    @lru_cache
    def installed_plugin_version(self) -> str:
        """Get plugin version installed."""
        assert (
            self.dst_plugin_dir.exists()
        ), f'Plugin not installed in "{self.dst_plugin_dir.as_posix()}", should not call this function'

        if self.engine_type == EngineEnum.blender:
            init_file = self.dst_plugin_dir / '__init__.py'
            _content = init_file.read_text()
            _match = re.search(r"__version__ = version = '(.*?)'", _content)
            if _match:
                dst_plugin_version = _match.groups()[0]
            else:
                dst_plugin_version = '0.0.0'  # cannot find version
        elif self.engine_type == EngineEnum.unreal:
            uplugin_file = self.dst_plugin_dir / f'{plugin_name_unreal}.uplugin'
            dst_plugin_version = json.loads(uplugin_file.read_text())['VersionName']
        else:
            raise NotImplementedError
        return dst_plugin_version

    def _download(self, url: str, dst_dir: Path) -> Path:
        """Check if the url is valid and download the plugin to the given directory."""
        try:
            dst_path = download(url=url, dst_dir=dst_dir, verbose=False)
        except HTTPError as e:
            raise HTTPError(
                url=e.url,
                code=e.code,
                msg=(
                    'Failed to download plugin.\n'
                    f'Sorry, pre-built plugin for {plugin_name_pattern.format(**self.plugin_info)} is not provided. '
                    'You can try to build the plugin from source.\n'
                    'Follow the instructions here: https://xrfeitoria.readthedocs.io/en/latest/faq.html#how-to-use-the-plugin-of-blender-unreal-under-development'
                ),
                hdrs=e.hdrs,
                fp=e.fp,
            )
        except URLError:
            raise RuntimeError(
                'Network unreachable. Please check your internet connection and try again later.\n'
                f'Or manually download the plugin from {url} and put it in "{dst_dir.as_posix()}"\n'
            )
        except Exception as e:
            raise RuntimeError(f'Failed to download plugin from {url} to "{dst_dir.as_posix()}"\n{e}')
        return dst_path

    # ----- abstracts ----- #
    ##########################

    @staticmethod
    @abstractmethod
    def _get_engine_info(engine_exec: Path) -> Tuple[str, str]:
        """Get engine type and version.

        Args:
            engine_exec (Path): path to engine executable.

        Returns:
            Tuple[str, str]: engine type and version.
        """
        pass

    @abstractmethod
    def _get_cmd(self) -> str:
        pass

    @abstractmethod
    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = '') -> subprocess.Popen:
        pass

    @property
    @lru_cache
    def plugin_info(self) -> plugin_info_type:
        plugin_infos: Dict[str, Dict[str, str]] = json.loads(plugin_infos_json.read_text())
        plugin_versions = sorted((map(parse, plugin_infos.keys())))
        _version = parse(__version__)

        # find compatible version, lower bound, e.g. 0.5.1 => 0.5.0
        if _version in plugin_versions:
            compatible_version = _version
        else:
            _idx = bisect_left(plugin_versions, parse(__version__)) - 1
            compatible_version = plugin_versions[_idx]

        # read from env (highest priority)
        if os.environ.get('XRFEITORIA__VERSION'):
            compatible_version = parse(os.environ['XRFEITORIA__VERSION'])

        logger.debug(f'Compatible plugin version: {compatible_version}')

        # get link
        if self.engine_type == EngineEnum.unreal:
            plugin_name = plugin_name_unreal
            engine_version = ''.join(self.engine_info)  # e.g. Unreal5.1
            _platform = platform.system()  # Literal["Windows", "Linux", "Darwin"]
        elif self.engine_type == EngineEnum.blender:
            plugin_name = plugin_name_blender
            engine_version = 'None'  # support all blender versions
            _platform = 'None'  # support all platforms
        plugin_version = os.environ.get('XRFEITORIA__VERSION') or plugin_infos[str(compatible_version)][plugin_name]
        # e.g. XRFeitoriaBpy-0.5.0-None-None
        # e.g. XRFeitoriaUnreal-0.5.0-Unreal5.1-Windows
        return dict(
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            engine_version=engine_version,
            platform=_platform,
        )

    @property
    @lru_cache
    def plugin_url(self) -> Optional[str]:
        if dist_root.startswith('http'):
            # e.g. https://github.com/openxrlab/xrfeitoria/releases/download/v0.6.2/XRFeitoriaBpy-0.6.2-None-None.zip
            # e.g. https://github.com/openxrlab/xrfeitoria/releases/download/v0.6.2/XRFeitoriaUnreal-0.6.2-Unreal5.1-Windows.zip
            plugin_version = self.plugin_info['plugin_version']
            plugin_filename = plugin_name_pattern.format(**self.plugin_info)
            plugin_url = f'{dist_root}/v{plugin_version}/{plugin_filename}.zip'
            return plugin_url
        else:
            # e.g. /path/to/dist/XRFeitoriaBpy-0.5.0-None-None.zip
            # e.g. /path/to/dist/XRFeitoriaUnreal-0.5.0-Unreal5.1-Windows.zip
            return f'{dist_root}/{plugin_name_pattern.format(**self.plugin_info)}.zip'

    def _install_plugin(self) -> None:
        """Install plugin."""
        if self.dst_plugin_dir.exists() and not self.replace_plugin:
            if parse(self.installed_plugin_version) < parse(self.plugin_info['plugin_version']):
                self.replace_plugin = True
            if (
                parse(self.installed_plugin_version) > parse(self.plugin_info['plugin_version'])
                and not self.replace_plugin
            ):
                logger.warning(
                    f'Plugin installed in "{self.dst_plugin_dir.as_posix()}" is in version {self.installed_plugin_version}, '
                    f'newer than version {self.plugin_info["plugin_version"]} which is required by {package_name}-{__version__}. '
                    'May cause unexpected errors.'
                )
            if not self.replace_plugin:
                logger.debug(f'Plugin "{self.dst_plugin_dir.as_posix()}" already exists')
                return
            elif self.engine_type == EngineEnum.unreal:
                logger.warning(f'Removing existing plugin "{self.dst_plugin_dir.as_posix()}"')
                _rmtree(self.dst_plugin_dir)

        src_plugin_path = self.get_src_plugin_path()
        logger.info(f'Installing plugin from "{src_plugin_path.as_posix()}" to "{self.dst_plugin_dir.as_posix()}"')

        if self.engine_type == EngineEnum.blender:
            _script = f"""
                import bpy;
                bpy.ops.preferences.addon_install(filepath='{src_plugin_path.as_posix()}');
                bpy.ops.preferences.addon_enable(module='{plugin_name_blender}');
                bpy.context.preferences.view.show_splash = False;
                bpy.ops.wm.save_userpref()"""

            cmd = self._get_cmd(python_scripts=dedent(_script).replace('\n', ''))
            process = self._popen(cmd)
            _code = process.wait()
            if _code != 0:
                logger.error(self.get_process_output(process))
                raise RuntimeError('Failed to install plugin for blender. Check the engine output above.')

        elif self.engine_type == EngineEnum.unreal:
            try:
                self.dst_plugin_dir.symlink_to(src_plugin_path, target_is_directory=True)
                logger.debug(f'Symlink "{src_plugin_path.as_posix()}" => "{self.dst_plugin_dir.as_posix()}"')
            except (OSError, PermissionError):
                logger.warning(
                    'Failed to create symlink: [u]permission denied[/u]. '
                    'Please consider running on [u]administrator[/u] mode. '
                    'Fallback to copy the plugin.'
                )
                shutil.copytree(src=src_plugin_path, dst=self.dst_plugin_dir)
                logger.debug(f'Copy "{src_plugin_path.as_posix()}" => "{self.dst_plugin_dir.as_posix()}"')

        logger.info(f'Plugin installed in "{self.dst_plugin_dir.as_posix()}"')

    @staticmethod
    @abstractmethod
    def test_connection(debug: bool = False) -> None:
        pass

    @staticmethod
    @abstractmethod
    def get_pid() -> int:
        pass


class BlenderRPCRunner(RPCRunner):
    def get_src_plugin_path(self) -> Path:
        """Get plugin source zip path."""
        if self.dev_plugin:
            from .publish_plugins import _make_archive

            src_plugin_dir = Path(__file__).resolve().parents[2] / 'src' / plugin_name_blender
            src_plugin_path = _make_archive(src_plugin_dir)
        else:
            src_plugin_root = tmp_dir / 'plugins'
            src_plugin_path = src_plugin_root / Path(self.plugin_url).name  # with suffix (.zip)
            if src_plugin_path.exists():
                logger.debug(f'Downloaded Plugin "{src_plugin_path.as_posix()}" exists')
                return src_plugin_path

            if self.plugin_url.startswith('http'):
                plugin_path = self._download(url=self.plugin_url, dst_dir=src_plugin_root)
            else:
                plugin_path = Path(self.plugin_url)
            if plugin_path != src_plugin_path:
                src_plugin_path.parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(plugin_path, src_plugin_path)
        return src_plugin_path

    @staticmethod
    def _get_engine_info(engine_exec: Path) -> Tuple[str, str]:
        _version = None
        if platform.system() == 'Darwin':
            root_dir = engine_exec.parent.parent / 'Resources'
        else:
            root_dir = engine_exec.parent
        for file in root_dir.iterdir():
            if not file.is_dir():
                continue
            # e.g. 3.3, 2.93
            if re.match(r'\d+\.\d+', file.name):
                _version = file.name
                break

        if _version is None:
            raise FileNotFoundError(f'Cannot find blender executable in {engine_exec.parent}')

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
            '--python-exit-code 1',
            f'--python-expr "{python_scripts}"' if python_scripts else '',
        ]
        return ' '.join(map(str, cmd))

    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = '') -> subprocess.Popen:
        """Start rpc server.

        Args:
            background (bool, optional): Run blender in background without GUI. Defaults to True.
            project_path (Optional[Path], optional): Path to blender project. Defaults to ''.

        Returns:
            subprocess.Popen: process of the engine started as rpc server.
        """
        # logger.info(f'Starting {" ".join(self.engine_info)} with RPC server at port {self.port}')

        # run server in blocking mode if background
        rpc_scripts = f'import bpy; bpy.ops.wm.start_rpc_servers(block={background}, port={self.port})'
        cmd = self._get_cmd(background=background, project_path=project_path, python_scripts=rpc_scripts)
        process = self._popen(cmd)

        self.wait_for_start(process=process)
        # logger.info(f'Started {" ".join(self.engine_info)} with RPC server at port {self.port}')
        return process

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

    @staticmethod
    @remote_blender(default_imports=[])
    def get_pid() -> int:
        """Get blender process id."""
        import os

        return os.getpid()


class UnrealRPCRunner(RPCRunner):
    """UnrealRPCRunner."""

    def get_src_plugin_path(self) -> Path:
        """Get plugin source directory."""
        if self.dev_plugin:
            src_plugin_path = Path(__file__).resolve().parents[2] / 'src' / plugin_name_unreal
            if not src_plugin_path.exists():
                raise FileNotFoundError(
                    f'Plugin source code not found in {src_plugin_path}, '
                    'please set `dev_plugin=False` to download the pre-built plugin. \n'
                    'Or clone the source code and build the plugin from source. '
                    'https://github.com/openxrlab/xrfeitoria.git'
                )
        elif self.plugin_url.startswith('http'):
            src_plugin_root = tmp_dir / 'plugins'
            src_plugin_compress = src_plugin_root / Path(self.plugin_url).name  # with suffix (.zip)
            src_plugin_path = src_plugin_compress.with_suffix('')  # without suffix (.zip)
            if src_plugin_path.exists():
                logger.debug(f'Downloaded Plugin "{src_plugin_path.as_posix()}" exists')
                return src_plugin_path
            elif src_plugin_compress.exists():
                logger.debug(f'Downloaded Plugin "{src_plugin_compress.as_posix()}" exists')
                shutil.unpack_archive(src_plugin_compress, src_plugin_root)
                assert src_plugin_path.exists(), f'Failed to unzip {src_plugin_compress} to {src_plugin_path}'
                return src_plugin_path

            plugin_compress = self._download(url=self.plugin_url, dst_dir=src_plugin_root)
            shutil.unpack_archive(plugin_compress, src_plugin_root)
            assert src_plugin_path.exists(), f'Failed to download plugin to {src_plugin_path}'
        else:
            # custom dist path
            plugin_compress = Path(self.plugin_url)
            src_plugin_path = plugin_compress.with_suffix('')  # without suffix (.zip)
        return src_plugin_path

    @staticmethod
    def _get_engine_info(engine_exec: Path) -> Tuple[str, str]:
        build_info = json.loads((engine_exec.parents[2] / 'Build' / 'Build.version').read_text())
        _version = f'{build_info["MajorVersion"]}.{build_info["MinorVersion"]}'
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

    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = '') -> subprocess.Popen:
        """Start rpc server.

        Args:
            background (bool, optional): Run unreal in background without GUI. Defaults to True.
            project_path (Optional[Path], optional): Path to unreal project. Defaults to ''.

        Returns:
            subprocess.Popen: process of the engine started as rpc server.
        """
        # logger.info(f'Starting {" ".join(self.engine_info)} with RPC server at port {self.port}')

        # run server in blocking mode if background
        cmd = self._get_cmd(
            background=background,
            project_path=project_path,
            rpc_port=self.port,
        )
        process = self._popen(cmd)

        # TODO: check if process is running
        self.wait_for_start(process=process)
        # logger.info(f'Started {" ".join(self.engine_info)} with RPC server at port {self.port}')
        return process

    @staticmethod
    @remote_unreal(default_imports=[])
    def test_connection(debug: bool = False) -> None:
        """Test connection."""
        import unreal

        unreal.log('Connection test passed')

    @staticmethod
    @remote_unreal(default_imports=[])
    def get_pid() -> int:
        """Get unreal process id."""
        import os

        return os.getpid()
