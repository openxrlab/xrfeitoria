import configparser
import platform
import shutil
from pathlib import Path
from typing import Literal, Union

from loguru import logger
from rich.prompt import Prompt

from ..data_structure.constants import ConfigDict, EngineEnum, PathLike
from ..data_structure.constants import config_path as default_config_path
from ..data_structure.constants import tmp_dir
from .downloader import download

# XXX: hard-coded blender download url
blender_compressed_urls = {
    'Windows': 'https://download.blender.org/release/Blender3.3/blender-3.3.10-windows-x64.zip',
    # 'Windows': 'https://mirrors.aliyun.com/blender/release/Blender3.3/blender-3.3.10-windows-x64.zip',
    'Darwin': None,
    'Linux': 'https://download.blender.org/release/Blender3.3/blender-3.3.10-linux-x64.tar.xz',
    # 'Linux': 'https://mirror.freedif.org/blender/release/Blender3.3/blender-3.3.10-linux-x64.tar.xz',
}


class Config:
    def __init__(self, engine: EngineEnum, path: PathLike = default_config_path) -> None:
        """Read config from config file.

        Args:
            path (Path, optional): Path to the config file. Defaults to config_path.
        """
        self.config: ConfigDict = {'blender_exec': None, 'unreal_exec': None}
        self.parser = configparser.ConfigParser()
        self.section_key = 'global'
        self.path = Path(path).resolve()
        self.engine = engine
        self.key = f'{self.engine.name.lower()}_exec'

        self.parser.read(self.path)
        if self.section_key not in self.parser.sections():
            # Create a new section, with default values
            self.parser.add_section(self.section_key)
            for key, value in self.config.items():
                self.parser.set(self.section_key, key, str(value))
        else:
            # Read config from file
            self.config = dict(self.parser[self.section_key])

    @property
    def exec_path(self) -> Path:
        """Path to engine executable."""
        if self.config.get(self.key) is None:
            path = Path(guess_exec_path(self.engine.name, raise_error=True)).resolve()
        else:
            path = Path(self.config[self.key]).resolve()
            if not path.exists():
                raise FileNotFoundError(f'"{self.path.as_posix()}": {self.key} invalid')
        return path

    @exec_path.setter
    def exec_path(self, value: PathLike) -> None:
        """Set the path to engine executable.

        Args:
            value (PathLike): Path to engine executable.

        Raises:
            FileNotFoundError: If the given executable is not valid.
        """
        value = Path(value).resolve()
        if not value.exists() or not value.is_file():
            raise FileNotFoundError(f'The given {self.engine.name} executable is not valid')
        self.config[self.key] = str(value)
        self.parser.set(self.section_key, self.key, value.as_posix())

    def write_config(self) -> None:
        """Write config to file, overwriting the original file.

        Raises:
            ValueError: If the config is not initialized or not valid.
        """
        if self.section_key not in self.parser.sections():
            raise ValueError('Config is not initialized or not valid')

        with open(self.path, 'w') as f:
            self.parser.write(f)
        logger.info(f'System config saved to "{self.path.as_posix()}"')

    @classmethod
    def update(cls, engine: Literal['blender', 'unreal'], exec_path: str) -> None:
        """Update a property in config file.

        Args:
            key (str): The key of the property.
            value (str): The value of the property.
        """
        config = cls(engine=EngineEnum[engine])
        config.exec_path = exec_path
        config.write_config()

    def __repr__(self) -> str:
        return f'Config(path="{self.path.as_posix()}", config={self.config})'


def download_engine(engine: Union[Literal['unreal', 'blender'], EngineEnum]) -> Path:
    """Download the engine executable.

    Args:
        engine (Union[Literal['unreal', 'blender'], EngineEnum]): The engine to download.

    Returns:
        Path: The path to the downloaded executable.
    """
    if not isinstance(engine, EngineEnum):
        engine = EngineEnum[engine]

    if engine == EngineEnum.unreal:
        raise NotImplementedError(
            'Sorry, automatic installing of unreal engine is not supported. \n'
            'Please download it manually from https://www.unrealengine.com/en-US/download'
        )
    elif engine == EngineEnum.blender:
        if platform.system() == 'Darwin':
            # not supported in MacOS
            raise NotImplementedError(
                'Sorry, automatic installing of blender engine on MacOS is not supported. \n'
                'Please download it manually from https://www.blender.org/download/'
            )

        dst_file = download(blender_compressed_urls[platform.system()], tmp_dir / 'programs')

        # get dst executable path
        filename = dst_file.stem.replace('.tar', '')  # remove .tar for linux
        dst_dir = dst_file.parent / filename
        # dst_file.unlink()  # remove compressed file
        exec_path = dst_dir / 'blender'
        if platform.system() == 'Windows':
            exec_path = exec_path.with_suffix('.exe')
        if exec_path.exists():
            return exec_path

        # uncompressed
        logger.info(f'Uncompressing "{dst_file.as_posix()}"')
        shutil.unpack_archive(dst_file, dst_file.parent)
        assert exec_path.exists(), f'Cannot find blender executable at {exec_path.as_posix()}'
        return exec_path


def guess_exec_path(engine: Union[Literal['unreal', 'blender'], EngineEnum], raise_error: bool = False) -> str:
    """Guess the executable path of the engine.

    Args:
        engine (Union[Literal['unreal', 'blender'], EngineEnum]): The engine to guess.
        raise_error (bool, optional): Whether to raise error if the executable is not found. Defaults to False.

    Raises:
        FileNotFoundError: If the executable is not found and `raise_error` is True.

    Returns:
        str: The executable path.
    """
    if not isinstance(engine, EngineEnum):
        engine = EngineEnum[engine]

    if engine == EngineEnum.unreal:
        path = shutil.which('UnrealEditor-Cmd')
        if path is None:
            # Hard-coded path
            if platform.system() == 'Windows':
                path = 'C:/Program Files/Epic Games/UE_5.2/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
            elif platform.system() == 'Linux':
                path = '/usr/bin/UnrealEditor-Cmd'
            elif platform.system() == 'Darwin':
                path = '/Applications/UnrealEngine/Engine/Binaries/Mac/UnrealEditor-Cmd'

    elif engine == EngineEnum.blender:
        path = shutil.which('blender')
        if path is None:
            # Hard-coded path
            if platform.system() == 'Windows':
                path = 'C:/Program Files/Blender Foundation/Blender 3.3/blender.exe'
            elif platform.system() == 'Linux':
                path = '/usr/bin/blender'
            elif platform.system() == 'Darwin':
                path = '/Applications/Blender.app/Contents/MacOS/Blender'

    if not Path(path).exists() and raise_error:
        raise FileNotFoundError(f'Cannot guess {engine.name} executable, please specify it manually')

    # logger.info(f'Guessed {engine.name} executable path: "{path}"')
    return path


def get_exec_path(
    engine: Union[Literal['unreal', 'blender'], EngineEnum],
    config_path: PathLike = default_config_path,
    to_install: bool = True,
    to_ask: bool = True,
) -> Path:
    """Get the executable path of the engine.
    Priority: system_config > guess > ask > install

    Args:
        engine (Union[Literal['unreal', 'blender'], EngineEnum]): The engine to get.
        to_install (bool, optional): Whether to install the engine if not found. Defaults to True.
        to_ask (bool, optional): Whether to ask for the executable path if not found. Defaults to True.


    Raises:
        FileNotFoundError: If the executable is not valid.

    Returns:
        Path: The executable path.
    """
    if not isinstance(engine, EngineEnum):
        engine = EngineEnum[engine]

    config = Config(engine=engine, path=config_path)

    # read from system config, if empty, guess
    try:
        return config.exec_path
    except FileNotFoundError:
        if not to_install and not to_ask:
            raise FileNotFoundError(f'{engine.name} executable not found')

    exec_path = ''
    # ask for path
    if to_ask:
        txt = f'Found no [bold]{engine.name}[/bold] executable in default config file ("{config.path.as_posix()}").\n'
        if engine == EngineEnum.blender:
            txt += (
                'Ways to solve this: \n'
                f'1. Press [bold]Enter[/bold] to download [bold]{engine.name}[/bold] automatically\n'
                f'2. Input path to executable (e.g. {guess_exec_path(engine)}) \n'
                '\[Enter]'
            )
        elif engine == EngineEnum.unreal:
            txt += f'Please input path to executable (e.g. {guess_exec_path(engine)}) \n'
        # input manually
        exec_path = Prompt.ask(txt)

    if to_install and exec_path == '':
        # auto download
        logger.info(f':robot: Automatically setup for {engine.name}')
        exec_path = download_engine(engine)
        config.exec_path = exec_path
        config.write_config()
    else:
        # from input
        config.exec_path = exec_path
        config.write_config()

    return config.exec_path


if __name__ == '__main__':
    # print(get_exec_path('blender'))
    Config.update('blender', 'C:/Program Files/Blender Foundation/Blender 3.3/blender.exe')
