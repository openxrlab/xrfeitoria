import json
import shutil
from pathlib import Path
from textwrap import dedent
from typing import Literal, Optional

from loguru import logger
from rich.prompt import Prompt

from xrfeitoria.data_structure.constants import tmp_dir
from xrfeitoria.utils import setup_logger
from xrfeitoria.utils.downloader import download
from xrfeitoria.utils.setup import Config, get_exec_path, guess_exec_path

# XXX: Hard-coded assets url
assets_url = dict(
    bunny='https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/stanford-bunny.obj',
    koupen_chan='https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/koupen_chan.fbx',
    SMPL_XL='https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/SMPL-XL-001.fbx',
    motion_1='https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/motion-greeting.fbx',
    motion_2='https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/motion-stand_to_walk_back.fbx',
    blend_sample='https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/Tree1.blend',
    hdr_sample='https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/hdr-sample.hdr',
)
# XXX: hard-coded unreal project url
unreal_sample_url = (
    'https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/unreal_project/XRFeitoriaUnreal_Sample.zip'
)
asset_dir = tmp_dir / 'assets'


def get_exec(engine: Literal['blender', 'unreal'], exec_from_config: Optional[Path] = None) -> str:
    """Ask for blender executable path.

    Args:
        engine (Literal['blender', 'unreal']): Engine name.
        engine_path_from_config (Optional[Path], optional): path of engine executable read from config. Defaults to None.
    """
    txt = f'Please input the path to the {engine} executable'

    # priority: exec_from_config > system_config (with guess) > ask > install
    if exec_from_config is not None:
        engine_path = Path(exec_from_config).resolve().as_posix()
    else:
        try:
            # system_config, if empty, guess
            engine_path = get_exec_path(engine=engine, to_ask=False, to_install=False).as_posix()
        except FileNotFoundError:
            engine_path = None
            txt += f' (e.g. {guess_exec_path(engine)})'
            if engine == 'blender':
                txt += ', or press [bold]enter[/bold] to install it'

    # ask
    path = Prompt.ask(txt, default=engine_path)
    if path is not None:
        path = Path(path.strip('"').strip("'")).resolve()
    else:
        if engine == 'unreal':
            raise FileNotFoundError('Please specify the path to the unreal executable.')
        # auto install for blender
        path = get_exec_path(engine=engine, to_ask=False, to_install=True)

    assert path.exists(), f'{engine} path {path.as_posix()} does not exist!'
    return path.as_posix()


def ask_unreal_project() -> str:
    """Ask for unreal project path."""
    txt = 'Please input the path to the unreal project, or press [bold]enter[/bold] to download a sample project\n\[Enter]'
    unreal_project = Prompt.ask(txt, default=None)
    return get_unreal_project(unreal_project)


def get_unreal_project(unreal_project: Optional[str] = None) -> str:
    """Retrieves the path of the Unreal project. If not provided, it will be downloaded
    and extracted.

    Args:
        unreal_project (Optional[str]): The path of the Unreal project. If not provided, it will be downloaded and extracted.

    Returns:
        str: The path of the Unreal project.

    Raises:
        FileNotFoundError: If the Unreal project does not exist.
    """
    if unreal_project is None:
        unreal_project_zip = download(url=unreal_sample_url, dst_dir=tmp_dir / 'unreal_project')
        shutil.unpack_archive(filename=unreal_project_zip, extract_dir=tmp_dir / 'unreal_project')
        unreal_project_dir = unreal_project_zip.parent / unreal_project_zip.stem
        unreal_project = next(unreal_project_dir.glob('*.uproject')).as_posix()
    unreal_project = unreal_project.strip('"').strip("'")
    if not Path(unreal_project).exists():
        config_file = Path(__file__).parent / 'config.py'
        logger.error(
            '[red]Error:[/red]\n'
            f'Unreal project "{unreal_project}" does not exist! \n'
            f'Config not set correctly, please [red]delete "{config_file.as_posix()}"[/red], and setup again.'
        )
        exit(1)
    return unreal_project


def main():
    try:
        from .config import blender_exec, unreal_exec, unreal_project
    except ImportError:
        blender_exec = unreal_exec = unreal_project = None

    setup_logger()
    engine = Prompt.ask('Which engine do you want to use?', choices=['blender', 'unreal'], default='blender')
    if engine == 'blender':
        blender_exec = get_exec('blender', exec_from_config=blender_exec)
        Config.update(engine=engine, exec_path=blender_exec)
    elif engine == 'unreal':
        unreal_exec = get_exec('unreal', exec_from_config=unreal_exec)
        unreal_project = ask_unreal_project(unreal_project=unreal_project)
        Config.update(engine=engine, exec_path=unreal_exec)

    assets_path = {}
    for idx, (name, url) in enumerate(assets_url.items()):
        logger.info(f'Downloading {idx+1}/{len(assets_url)}: {name}')
        save_path = download(url, dst_dir=asset_dir / name)
        # save the path
        assets_path[name] = save_path.as_posix()

    # write the config file
    config_path = Path(__file__).parent / 'config.py'
    with open(config_path, 'w') as f:
        _keys = {key: 'str' for key in assets_path.keys()}
        _config = dedent(
            f"""\
            from typing import TypedDict

            blender_exec = {repr(blender_exec)}
            unreal_exec = {repr(unreal_exec)}
            unreal_project = {repr(unreal_project)}

            assets_path_type = TypedDict('assets_path', {json.dumps(_keys)})
            assets_path: assets_path_type = {json.dumps(assets_path)}"""
        )
        f.write(_config)
    logger.info(f'Saved config to "{config_path}"')


if __name__ == '__main__':
    main()
