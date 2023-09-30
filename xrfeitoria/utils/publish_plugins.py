"""Publish plugins to zip files.

>>> python -m xrfeitoria.utils.publish_plugins --unreal -s 0.5.0-UE5.2-Windows
>>> python -m xrfeitoria.utils.publish_plugins --blender -s 0.5.0-None-None
"""
from pathlib import Path
from typing import Literal, Optional

from loguru import logger

from .. import __version__
from ..data_structure.constants import PathLike, plugin_name_blender, plugin_name_unreal

root = Path(__file__).parent.resolve()
project_root = root.parents[1]


def _make_archive(
    plugin_folder: PathLike,
    zip_name: Optional[str] = None,
    folder_name: Optional[str] = None,
) -> Path:
    """Make archive of plugin folder.

    Args:
        plugin_folder (PathLike): path to plugin folder.
        zip_name (Optional[str], optional): name of the archive file.
            E.g. dst_name='plugin', the archive file would be ``plugin.zip``.
            Defaults to None, fallback to {plugin_folder.name}.
    """
    import zipfile

    if zip_name is None:
        zip_name = plugin_folder.name
    if folder_name is None:
        folder_name = zip_name

    plugin_folder = Path(plugin_folder).resolve()
    plugin_zip = plugin_folder.parent / f'{zip_name}.zip'
    if plugin_zip.exists():
        plugin_zip.unlink()

    filter_names = ['.git', '.idea', '.vscode', '.gitignore', '.DS_Store', '__pycache__', 'Intermediate']
    with zipfile.ZipFile(plugin_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        for file in plugin_folder.rglob('*'):
            # filter
            if any([folder in file.parts for folder in filter_names]):
                continue

            # in zip, the folder name is the root folder
            # {folder_name}/a/b/c
            arcname = folder_name + '/' + file.relative_to(plugin_folder).as_posix()
            zipf.write(file, arcname=arcname)

    # plugin_folder = shutil.make_archive(plugin_zip.with_suffix(''), 'zip', plugin_folder.parent, plugin_folder.name)
    logger.debug(f'Compressed {plugin_folder} => {plugin_zip}')
    return plugin_zip


def main(engine: Literal['unreal', 'blender'], suffix: Optional[str] = None):
    if engine == 'blender':
        plugin_name = plugin_name_blender
        folder_name = plugin_name  # in zip, {XRFeitoriaBpy} is the root folder
    elif engine == 'unreal':
        # TODO: auto detect binaries
        plugin_name = plugin_name_unreal
        folder_name = None  # in zip, {XRFeitoriaUnreal-x.x.x-UE5.x-Windows} is the root folder

    dir_plugin = project_root / 'src' / plugin_name

    name = plugin_name
    if suffix is not None:
        name += f'-{suffix}'
    else:
        name += f'-{__version__}'
    plugin_zip = _make_archive(dir_plugin, zip_name=name, folder_name=folder_name)
    logger.info(f'Plugin for {engine}: {plugin_zip}')


if __name__ == '__main__':
    from typer import Option, run

    def wrapper(
        unreal: bool = Option(False, '--unreal', '-u', help='Build plugin for Unreal'),
        blender: bool = Option(False, '--blender', '-b', help='Build plugin for Blender'),
        suffix: str = Option(
            None,
            '--suffix',
            '-s',
            help='Suffix of the compressed file, e.g. "XRFeitoriaUnreal-{suffix}.zip". if None, use version number',
        ),
    ):
        if unreal:
            main(engine='unreal', suffix=suffix)
        if blender:
            main(engine='blender', suffix=suffix)

    run(wrapper)
