import json
from pathlib import Path
from textwrap import dedent
from typing import Optional

from loguru import logger

from xrfeitoria.utils import setup_logger
from xrfeitoria.utils.downloader import download
from xrfeitoria.utils.setup import Config

from .setup import asset_dir, assets_url, get_unreal_project


def main(blender_exec: Optional[str] = None, unreal_exec: Optional[str] = None):
    setup_logger()
    if blender_exec:
        Config.update(engine='blender', exec_path=blender_exec)
    if unreal_exec:
        Config.update(engine='unreal', exec_path=unreal_exec)

    unreal_project = get_unreal_project()
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
    from typer import Option, run

    def wrapper(
        blender_exec: Optional[str] = Option(None, '-b', help='Path to Blender executable'),
        unreal_exec: Optional[str] = Option(None, '-u', help='Path to Unreal Engine executable'),
    ):
        main(blender_exec, unreal_exec)

    run(wrapper)
