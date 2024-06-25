"""Publish plugins to zip files.

>>> python -m xrfeitoria.utils.publish_plugins --help
"""

import json
import os
import platform
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger
from packaging.version import parse
from typer import Option, Typer

from ..data_structure.constants import plugin_name_blender, plugin_name_pattern, plugin_name_unreal
from ..utils import setup_logger
from ..version import __version__, __version_tuple__
from .runner import UnrealRPCRunner

root = Path(__file__).parent.resolve()
project_root = root.parents[1]
src_root = project_root / 'src'
dist_root = src_root / 'dist'
dist_root.mkdir(exist_ok=True, parents=True)
plugin_infos_json = root / 'plugin_infos.json'

setup_logger(level='INFO')
app = Typer(pretty_exceptions_show_locals=False)


@contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def _make_archive(
    src_folder: Path,
    dst_path: Optional[Path] = None,
    folder_name_inside_zip: Optional[str] = None,
    filter_names: Tuple[str, ...] = ('.git', '.vscode', '.gitignore', '.DS_Store', '__pycache__', 'Intermediate'),
) -> Path:
    """Make archive of plugin folder.

    Zip Plugin folder to ``{plugin_folder.parent}/{zip_name}.zip``.

    Args:
        plugin_folder (Path): path to plugin folder.
        zip_name (Optional[str], optional): name of the archive file. E.g. dst_name='plugin', the archive file would be ``plugin.zip``.
            Defaults to None, fallback to {plugin_folder.name}.
        folder_name (Optional[str], optional): name of the root folder in the archive.
        filter_names (Tuple[str, ...], optional): names of folders to be ignored.
            Defaults to ('.git', '.vscode', '.gitignore', '.DS_Store', '__pycache__', 'Intermediate').
    """
    import zipfile

    if dst_path is None:
        dst_path = src_folder.parent / f'{src_folder.name}.zip'
    if folder_name_inside_zip is None:
        folder_name_inside_zip = dst_path.stem

    if dst_path.exists():
        dst_path.unlink()
    dst_path.parent.mkdir(exist_ok=True, parents=True)

    with zipfile.ZipFile(dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        for file in src_folder.rglob('*'):
            # filter
            if any([folder in file.parts for folder in filter_names]):
                continue

            # in zip, the folder name is the root folder
            # {folder_name_inside_zip}/a/b/c
            arcname = folder_name_inside_zip + '/' + file.relative_to(src_folder).as_posix()
            zipf.write(file, arcname=arcname)

    logger.info(f'Compressed {src_folder} => {dst_path}')
    return dst_path


@app.command()
def update_plugin_info():
    """Update version infos in plugin files."""
    package_version = str(parse(__version__))

    bpy_version = (src_root / plugin_name_blender / '__init__.py').read_text()
    bpy_version = re.search(r"__version__ = version = '(.*)'", bpy_version).group(1)

    unreal_version = (src_root / plugin_name_unreal / f'{plugin_name_unreal}.uplugin').read_text()
    unreal_version = re.search(r'"VersionName": "(.*)"', unreal_version).group(1)

    plugin_infos: Dict[str, Dict[str, str]] = json.loads(plugin_infos_json.read_text())
    plugin_infos[package_version] = {
        'XRFeitoria': package_version,
        'XRFeitoriaBpy': str(parse(bpy_version)),
        'XRFeitoriaUnreal': str(parse(unreal_version)),
    }
    plugin_infos = dict(sorted(plugin_infos.items(), key=lambda item: parse(item[0]), reverse=True))  # sort by version
    plugin_infos_json.write_text(json.dumps(plugin_infos, indent=4) + '\n')  # dump to json
    logger.info(f'Updated "{plugin_infos_json}" with version {package_version}')


@app.command()
def update_bpy_version(bpy_init_file: Path = src_root / plugin_name_blender / '__init__.py'):
    """Update version in ``src/XRFeitoriaBpy/__init__.py``.

    Args:
        bpy_init_file (Path): path to ``__init__.py`` file.
    """
    content = bpy_init_file.read_text()
    # update version
    content = re.sub(pattern=r"'version': \(.*\)", repl=f"'version': {__version_tuple__}", string=content)
    content = re.sub(
        pattern=r'__version__ = version = .*', repl=f"__version__ = version = '{__version__}'", string=content
    )
    bpy_init_file.write_text(content)
    logger.info(f'Updated "{bpy_init_file}" with version {__version__}')


@app.command()
def update_uplugin_version(uplugin_path: Path = src_root / plugin_name_unreal / f'{plugin_name_unreal}.uplugin'):
    """Update version in ``src/XRFeitoriaUnreal/XRFeitoria.uplugin``.

    Args:
        uplugin_file (Path): path to ``XRFeitoria.uplugin`` file.
    """
    content = uplugin_path.read_text()
    # update version
    content = re.sub(pattern=r'"VersionName": ".*"', repl=f'"VersionName": "{__version__}"', string=content)
    uplugin_path.write_text(content)
    logger.info(f'Updated "{uplugin_path}" with version {__version__}')


@app.command()
def build_blender():
    """Publish Blender Plugin to zip files.

    Examples:

    >>> python -m xrfeitoria.utils.publish_plugins build-blender
    """
    plugin_name = plugin_name_pattern.format(
        plugin_name=plugin_name_blender,
        plugin_version=__version__,
        engine_version='None',
        platform='None',
    )  # e.g. XRFeitoriaBlender-0.5.0-None-None
    dir_plugin = src_root / plugin_name_blender
    update_bpy_version(dir_plugin / '__init__.py')

    plugin_zip = _make_archive(
        src_folder=dir_plugin,
        dst_path=dist_root / f'{plugin_name}.zip',
        folder_name_inside_zip=plugin_name_blender,
    )
    dst_plugin_zip = dist_root / plugin_zip.name
    logger.info(f'Plugin for blender: "{dst_plugin_zip}"')


@app.command()
def build_unreal(
    unreal_exec_list: List[Path] = Option(
        None,
        '-u',
        '--unreal-exec',
        resolve_path=True,
        file_okay=True,
        dir_okay=False,
        exists=True,
        help='Path to Unreal Engine executable. e.g. "C:/Program Files/Epic Games/UE_5.1/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"',
    ),
):
    """Publish Unreal Plugin to zip files.

    Examples:

    >>> python -m xrfeitoria.utils.publish_plugins build-unreal
    -u "C:/Program Files/Epic Games/UE_5.1/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    -u "C:/Program Files/Epic Games/UE_5.2/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    -u "C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    """
    dir_plugin = src_root / plugin_name_unreal
    uplugin_path = dir_plugin / f'{plugin_name_unreal}.uplugin'
    update_uplugin_version(uplugin_path)
    logger.info('Compiling plugin for Unreal Engine...')
    suffix = 'bat' if platform.system() == 'Windows' else 'sh'
    for unreal_exec in unreal_exec_list:
        uat_path = unreal_exec.parents[2] / f'Build/BatchFiles/RunUAT.{suffix}'
        unreal_infos = UnrealRPCRunner._get_engine_info(unreal_exec)
        engine_version = ''.join(unreal_infos)  # e.g. Unreal5.1
        plugin_name = plugin_name_pattern.format(
            plugin_name=plugin_name_unreal,
            plugin_version=__version__,
            engine_version=engine_version,
            platform=platform.system(),
        )  # e.g. XRFeitoriaUnreal-0.6.0-Unreal5.3-Windows
        plugin_src_name = plugin_name_pattern.format(
            plugin_name=plugin_name_unreal,
            plugin_version=__version__,
            engine_version=engine_version,
            platform='Source',
        )  # e.g. XRFeitoriaUnreal-0.6.0-Unreal5.3-Source
        dist_path = src_root / plugin_name
        subprocess.call([uat_path, 'BuildPlugin', f'-Plugin={uplugin_path}', f'-Package={dist_path}'])
        _make_archive(src_folder=dist_path, dst_path=dist_root / f'{plugin_name}.zip')
        _make_archive(
            src_folder=dist_path,
            dst_path=dist_root / f'{plugin_src_name}.zip',
            folder_name_inside_zip=plugin_name_unreal,
            filter_names=('.DS_Store', '__pycache__', 'Intermediate', 'Binaries'),
        )
        logger.info(f'Plugin for {engine_version}: "{dist_path}.zip"')


if __name__ == '__main__':
    app()
