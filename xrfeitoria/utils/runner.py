import platform
import random
import re
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from textwrap import dedent
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, Union

import psutil
from loguru import logger
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

from ..constants import (
    PathLike,
    __regex_frame_info__,
    __regex_range_info__,
    plugin_name_blender,
    plugin_name_unreal,
)
from ..rpc import BLENDER_PORT, UNREAL_PORT, remote_blender_decorator, remote_unreal_decorator
from .tools import Logger


def _rmtree(path: Path) -> None:
    """remove tmp output"""
    if path.is_symlink():
        path.unlink()
    else:
        shutil.rmtree(path)


def _mklink(src: Path, dst: Path) -> None:
    if platform.system() == "Windows":
        mklink = ["cmd", "/c", "mklink", "/d", str(dst), str(src)]
    else:
        mklink = ["ln", "-s", str(src), str(dst)]
    subprocess.check_call(mklink)


def _get_user_addon_path(version: str) -> Path:
    user_path = Path.home()
    if platform.system() == "Windows":
        user_addon_path = user_path / f"AppData/Roaming/Blender Foundation/Blender/{version}/scripts/addons"
    elif platform.system() == "Linux":
        user_addon_path = user_path / f".config/blender/{version}/scripts/addons"
    elif platform.system() == "Darwin":
        user_addon_path = user_path / f"Library/Application Support/Blender/{version}/scripts/addons"
    return user_addon_path


def _make_archive(plugin_folder: Union[Path, str]) -> Path:
    """make archive of plugin folder"""
    plugin_folder = Path(plugin_folder).resolve()
    plugin_zip = plugin_folder.with_suffix(".zip")
    if plugin_zip.exists():
        plugin_zip.unlink()
    plugin_folder = shutil.make_archive(plugin_folder, "zip", plugin_folder.parent, plugin_folder.name)
    return plugin_zip


class RPCRunner(ABC):
    """A wrapper for starting blender as a rpc server"""

    def __init__(
        self,
        engine_exec: Optional[PathLike] = None,
        project_path: Optional[PathLike] = "",
        replace_plugin: bool = False,
        background: bool = True,
        new_process: bool = True,
    ) -> None:
        self.engine_process: Optional[subprocess.Popen] = None
        self.engine_exec = Path(engine_exec).resolve() if engine_exec else self.guess_exec_path()
        if not self.engine_exec.exists():
            raise FileExistsError(f"Engine executable not found: {self.engine_exec}")
        self.project_path = Path(project_path).resolve() if project_path else None
        self.engine_version = self._get_engine_version(self.engine_exec)
        self.replace_plugin = replace_plugin
        self.background = background
        self.new_process = new_process

    def __enter__(self) -> "RPCRunner":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()

    def __del__(self) -> None:
        if self.engine_process is not None:
            self.stop()

    def stop(self) -> None:
        process = self.engine_process
        if process is not None:
            logger.info("Exiting RPCRunner, killing engine process")
            for child in psutil.Process(process.pid).children(recursive=True):
                if child.is_running():
                    logger.debug(f"Killing child process {child.pid}")
                    child.kill()
            process.kill()
            self.engine_process = None
        else:
            logger.debug("Exiting RPCRunner, the engine process won't stop due to not started by this RPCRunner.")

    @staticmethod
    def _popen(cmd) -> subprocess.Popen:
        """execute command"""
        logger.debug(f"Executing command:\n{cmd}")
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        return process

    def start(self):
        """start rpc server"""
        if not self.new_process:
            logger.debug("Trying to reuse existing process (finding existing engine process)")
            try:
                self.test_connection()
                logger.info("Connection successful, reusing existing process (existing engine process found)")
                return
            except ConnectionRefusedError:
                logger.debug("Connection refused, starting new process (although new_process=False)")

        self._install_plugin(replace=self.replace_plugin)
        self._start_rpc(background=self.background, project_path=self.project_path)

    ##########################
    # ----- abstracts ----- #
    ##########################

    @staticmethod
    @abstractmethod
    def _get_engine_version(engine_exec: Path) -> str:
        pass

    @abstractmethod
    def _get_cmd(self):
        pass

    @abstractmethod
    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = "") -> None:
        pass

    @abstractmethod
    def _install_plugin(self, replace: bool = False) -> None:
        pass

    @staticmethod
    @abstractmethod
    def test_connection() -> None:
        pass

    @staticmethod
    @abstractmethod
    def guess_exec_path() -> str:
        pass


class BlenderRPCRunner(RPCRunner):
    @staticmethod
    def _get_engine_version(blender_exec: Path) -> str:
        """get blender version"""
        return next(blender_exec.parent.glob("*.*")).name

    def _get_cmd(
        self,
        background: bool = True,
        project_path: Optional[Path] = "",
        python_scripts: Optional[str] = "",
    ) -> str:
        """get blender command line"""
        cmd = [
            f'"{self.engine_exec}"',
            "--background" if background else "",
            f'"{project_path}"' if project_path else "",
            f'--python-expr "{python_scripts}"' if python_scripts else "",
        ]
        return " ".join(map(str, cmd))

    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = "") -> None:
        """start rpc server"""
        try:
            # TODO: too slow in test
            self.test_connection()
            raise RuntimeError(
                f"RPC server in `RPC_PORT={BLENDER_PORT}` already started! This is raised when calling `init_blender(new_process=True)`. 3 ways to get around this: \n"
                "   1. set `new_process=False` to use the existing server. \n"
                "   2. stop the server (blender process) and try again; \n"
                "   3. change the rpc port via system env 'RPC_PORT' and try again; \n"
            )
        except ConnectionError:
            pass

        # run server in blocking mode if background
        logger.info(f"Starting blender {self.engine_version} with RPC server at port {BLENDER_PORT}")
        rpc_scripts = f"import bpy; bpy.ops.wm.start_rpc_servers(block={background}, port={BLENDER_PORT})"
        cmd = self._get_cmd(
            background=background,
            project_path=project_path,
            python_scripts=rpc_scripts,
        )
        process = self._popen(cmd)

        # try to connect to the server
        # if cannot connect, raise an error
        tryout_times = 0
        while True:
            try:
                self.test_connection()
                break
            except ConnectionRefusedError:
                logger.debug("Waiting for RPC server to start")
                tryout_times += 1
                time.sleep(5)
            if tryout_times >= 5:
                raise ConnectionRefusedError("RPC server not started")

        logger.info(f"Started blender {self.engine_version} with RPC server at port {BLENDER_PORT}")
        self.engine_process = process

    def _install_plugin(self, replace: bool = False) -> None:
        """install blender plugin"""
        plugin_path = _get_user_addon_path(self.engine_version) / plugin_name_blender
        plugin_installed = plugin_path.exists()
        if not replace and plugin_installed:
            logger.debug(f"Plugin {plugin_name_blender} already installed")
            return

        logger.info(f"Installing blender plugin: {plugin_name_blender}")
        plugin_path = Path(__file__).resolve().parent.parent.parent / "src" / plugin_name_blender
        if not plugin_path.exists():
            logger.error(f"Plugin not found in {plugin_path}")
            raise FileNotFoundError(f"Plugin not found in {plugin_path}")
        plugin_path = _make_archive(plugin_path)
        _script = f"""
            import bpy;
            bpy.ops.preferences.addon_install(filepath='{plugin_path.as_posix()}');
            bpy.ops.preferences.addon_enable(module='{plugin_name_blender}');
            bpy.ops.wm.save_userpref()"""

        cmd = self._get_cmd(python_scripts=dedent(_script).replace("\n", ""))
        process = self._popen(cmd)
        process.wait()
        logger.info("Plugin installed")

    @staticmethod
    @remote_blender_decorator
    def test_connection() -> bool:
        """test connection"""
        print("Connection test passed")

    @staticmethod
    def guess_exec_path() -> str:
        path = shutil.which("blender")
        if path is None:
            raise FileNotFoundError("Cannot find blender executable, please specify it manually")
        return path


class UnrealRPCRunner(RPCRunner):
    """UnrealRPCRunner"""

    @staticmethod
    def _get_engine_version(unreal_exec: Path) -> str:
        """get unreal version"""
        return re.findall(r"UE_(\d+\.\d+)", unreal_exec.as_posix())[0]

    def _get_cmd(
        self,
        project_path: PathLike,
        background: bool = True,
        # python_scripts: Optional[str] = "",
        rpc_port: int = 9998,
    ) -> str:
        assert not background, NotImplementedError("UnrealRPCRunner only support foreground mode for now")
        rpc_scripts = "import unreal; bootstrap_unreal_with_rpc_server(block=True)"
        cmd = [
            f'"{self.engine_exec}"',
            f'"{project_path}"',
            f'-run=pythonscript -script="{rpc_scripts}"' if background else "",
            # f'-ExecutePythonScript="{python_script_path}"',
            # f'-ExecCmds="py {python_script_path}"',
            f"-rpc_port={rpc_port}" "-notexturestreaming",
            "-silent",
            "LOG=Pipeline.log",
            "-LOCALLOGTIMES",
        ]
        return " ".join(map(str, cmd))

    def _start_rpc(self, background: bool = True, project_path: Optional[Path] = "") -> None:
        """start rpc server"""
        try:
            self.test_connection()
            raise RuntimeError(
                f"RPC server in `RPC_PORT={UNREAL_PORT}` already started! 3 ways to get around this: \n"
                "1. stop the server and try again; \n"
                "2. change the rpc port via system env 'RPC_PORT' and try again; \n"
                "3. set `new_process=False` to use the existing server."
            )
        except ConnectionError:
            pass

        # run server in blocking mode if background
        logger.info(f"Starting UE {self.engine_version} with RPC server at port {UNREAL_PORT}")
        cmd = self._get_cmd(
            background=background,
            project_path=project_path,
            rpc_port=UNREAL_PORT,
        )
        process = self._popen(cmd)

        tryout_times = 0
        while tryout_times < 5:
            try:
                self.test_connection()
                break
            except ConnectionRefusedError:
                logger.debug("Waiting for RPC server to start")
                tryout_times += 1
                time.sleep(5)

        logger.info(f"UE {self.engine_version} with RPC server started at port {UNREAL_PORT}")
        self.engine_process = process

    def _install_plugin(self, replace: bool = False) -> None:
        """install plugin"""
        project_dir = self.project_path.parent

        src_plugin_path = Path(__file__).resolve().parent.parent.parent / "src" / plugin_name_unreal
        dst_plugin_dir = project_dir / "Plugins" / plugin_name_unreal
        dst_plugin_dir.parent.mkdir(exist_ok=True)

        # check if the plugin is already linked
        if dst_plugin_dir.exists():
            if replace:
                logger.warning(f"Removing existing plugin {dst_plugin_dir}")
                _rmtree(dst_plugin_dir)
            else:
                logger.debug(f"Plugin {dst_plugin_dir} already exists")
                return

        logger.info(f"Installing plugin (symlink) to {project_dir}")
        _mklink(src=src_plugin_path, dst=dst_plugin_dir)

    @staticmethod
    @remote_unreal_decorator
    def test_connection() -> None:
        """test connection"""
        import unreal  # fmt: skip
        unreal.log("Connection test passed")

    @staticmethod
    def guess_exec_path() -> str:
        path = shutil.which("UnrealEditor-Cmd")
        if path is None:
            raise FileNotFoundError("Cannot find Unreal executable, please specify it manually")
        return path


class BlenderScriptRunner:
    """A wrapper for running blender script in python"""

    def __init__(self, blender_command: Path, blender_script: Path) -> None:
        self.blender_command = blender_command
        self.blender_script = blender_script
        self.frame_now = -1
        self.frame_count = 0
        self.frame_range: Optional[Tuple[int, int]] = None
        self.frame_total = 0
        self.pbar = None
        self.render_output = Path("~/.tmp").expanduser() / f"{random.randint(0, 1e6):06d}"

    def _get_cmd(self, blend_file: Optional[Path] = "", *args, **kwargs) -> str:
        """get blender command line"""
        _line_break = "\n\t"
        if platform.platform().startswith("Windows"):
            _line_break = " "
        cmd = [
            f'"{self.blender_command}"',
            f'-b "{blend_file}"',
            f'--render-output "{self.render_output}"',
            f'--python "{self.blender_script}" --',
        ]
        args_flag = []
        for key, value in kwargs.items():
            if value is None:
                continue
            key = key.replace("_", "-")
            if type(value) is list or type(value) is tuple:
                value = map(str, value)
                value = " ".join(value)
            _flag = f"--{key} {value}"
            args_flag.append(_flag)

        cmd.extend(args_flag)
        cmd = _line_break.join(map(str, cmd))
        return cmd

    @staticmethod
    def _popen(cmd) -> subprocess.Popen:
        """execute command"""
        logger.debug(f"Executing command:\n{cmd}")  # log
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        return process

    def reset(self) -> None:
        """reset"""
        if self.pbar:
            self.pbar.close()
            self.pbar = None

        self.frame_now = -1
        self.frame_count = 0
        self.frame_range: Optional[Tuple[int, int]] = None
        self.frame_total = 0

    def _match_frame_range(self, line: str) -> bool:
        """match frame range from blender output,
            and set self.frame_range.
            return True if matched, else return False

        Args:
            line (str): line of blender output

        Returns:
            bool: True if matched, else return False
        """
        matched_frame_range = re.match(__regex_range_info__, line)
        if matched_frame_range:
            frame_start = int(matched_frame_range.group(1))
            frame_end = int(matched_frame_range.group(2))
            self.frame_range = (frame_start, frame_end)
            self.frame_total = frame_end - frame_start + 1
            return True
        return False

    def _match_render_info(self, line: str) -> bool:
        """match render info from blender output,
            and set self.frame_now.
            return True if matched, else return False

        Args:
            line (str): line of blender output

        Returns:
            bool: True if matched, else return False
        """
        matched_frame_info = re.match(__regex_frame_info__, line)
        if matched_frame_info:
            _frame_now = int(matched_frame_info.group(1))
            if _frame_now != self.frame_now:
                self.frame_now = _frame_now
                self.frame_count += 1
                return True
        return False

    def _handle_line(self, line: str, interval: int = 50) -> None:
        """handle line of blender output"""
        if self.frame_range is None:
            if self._match_frame_range(line):
                logger.info("Start rendering")

        if self._match_render_info(line):
            # log every interval frames
            if self.frame_count % interval != 0:
                return
            # log with frame range
            if self.frame_range:
                logger.info(f"Rendering step: {self.frame_count}/{self.frame_total}")
            # log without frame range
            else:
                logger.info(f"Rendering step: {self.frame_count}")

    def _handle_line_with_tqdm(self, line: str, interval: int = 1) -> None:
        # TODO: log to file
        if self.frame_range is None:
            if self._match_frame_range(line):
                logger.info("Start rendering:")
                self.pbar = tqdm(total=self.frame_total)

        if self._match_render_info(line):
            if self.pbar is None:
                self.pbar = tqdm()
            # log every interval frames
            if self.frame_count % interval != 0:
                return
            # log with frame range
            if self.frame_range:
                self.pbar.update(interval)
            # log without frame range
            else:
                self.pbar.update(interval)

    def _handle_process(self, process: subprocess.Popen, lines: List[str]) -> List[str]:
        """handle blender process"""
        for line in iter(process.stdout.readline, ""):
            if line:
                line = line.decode()
                lines.append(line)
                # self._handle_line(line)
                self._handle_line_with_tqdm(line)
            else:
                break

        self.reset()

    def _log_errors(self, cmd: str, lines: List[str]) -> str:
        """format lines of blender output"""
        _info = (
            "\n\n===============================================================\n\n"
            + "".join(lines)
            + "\n\n===============================================================\n\n"
        )
        _log_file = Logger.find_logger_file()

        logger.error(f"[*] Error command:\n{cmd}")
        logger.error(f"[*] Error lines:\n{_info}")
        logger.error(f"[*] Error log file: {_log_file}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        before_sleep=before_sleep_log(logger=logger, log_level="WARNING"),
    )
    def _run_process(self, cmd) -> bool:
        """run blender process, return True if success, else return False"""
        try:
            process = self._popen(cmd)
            lines = []
            self._handle_process(process, lines)
        except KeyboardInterrupt as e:
            import psutil

            for child in psutil.Process(process.pid).children(recursive=True):
                child.kill()
            process.kill()
            logger.warning("KeyboardInterrupt, kill blender process")
            return False
        except subprocess.CalledProcessError as e:
            out_bytes = e.output
            code = e.returncode
            logger.error(f"[*] Error code: {code}")
            logger.error(f"[*] Error output:\n{out_bytes.decode()}")
            self._log_errors(cmd=cmd, lines=lines)
            raise e

        if any(["Error: Python:" in l for l in lines]):
            self._log_errors(cmd=cmd, lines=lines)
            raise RuntimeError("Blender Python Error")

        return True

    def run(self, blend_file: Optional[Path] = "", *args, **kwargs) -> bool:
        """run blender, return True if success, else return False"""
        self.render_output.mkdir(parents=True, exist_ok=True)
        cmd = self._get_cmd(blend_file=blend_file, *args, **kwargs)
        is_success = self._run_process(cmd=cmd)
        shutil.rmtree(self.render_output)  # remove tmp output
        return is_success
