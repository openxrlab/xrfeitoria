"""
>>> python -m samples.unreal.01_add_shapes

This is a script to add shapes in unreal.
"""

from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.utils import setup_logger

from ..config import unreal_exec, unreal_project

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/samples/unreal/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
default_level = '/Game/Levels/Default'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO')

    # unreal will start in a separate process in RPC Server mode automatically,
    # and close using `xf_runner.close()`
    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # open a level, this can be omitted if you don't need to open a level
    xf_runner.utils.open_level(default_level)

    # We provide many useful functions that you can accomplish complex tasks without knowing unreal API.
    # like spawn a shape
    scale = 0.4
    height = 0.4

    # spawn cube
    for idx in range(4):
        xf_runner.Shape.spawn(
            type='cube',
            name=f'cube_{idx}',
            location=(0, idx, height),
            scale=(scale, scale, scale),
        )
    # spawn sphere
    for idx in range(4):
        xf_runner.Shape.spawn(
            type='sphere',
            name=f'sphere_{idx}',
            location=(1, idx, height),
            scale=(scale, scale, scale),
        )
    # spawn cylinder
    for idx in range(4):
        xf_runner.Shape.spawn(
            type='cylinder',
            name=f'cylinder_{idx}',
            location=(2, idx, height),
            scale=(scale, scale, scale),
        )
    # spawn cone
    for idx in range(4):
        xf_runner.Shape.spawn(
            type='cone',
            name=f'cone_{idx}',
            location=(3, idx, height),
            scale=(scale, scale, scale),
        )

    # Save the unreal project
    # xf_runner.utils.save_current_level()

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # close the unreal process
    xf_runner.close()

    logger.info(f'You can check the result with Unreal in: "{unreal_project}"')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
