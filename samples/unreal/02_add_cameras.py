"""
>>> python -m samples.unreal.02_add_cameras

This is a script to add cameras in unreal.
"""
import math
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.utils import setup_logger

from ..config import unreal_exec, unreal_project

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/samples/unreal/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'unreal.log'
default_level = '/Game/Levels/Default'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)
    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # open a level, this can be omitted if you don't need to open a level
    xf_runner.utils.open_level(default_level)

    # add 32 circled cameras around the center
    center = (1, 2, 1)
    distance = 2
    fov = 90

    for idx in range(32):
        azimuth = 360 / 32 * idx
        azimuth_radians = math.radians(azimuth)

        x = distance * math.cos(azimuth_radians) + center[0]
        y = distance * math.sin(azimuth_radians) + center[1]
        z = 0.0 + center[2]
        location = (x, y, z)

        camera = xf_runner.Camera.spawn(
            camera_name=f'camera_{idx}',
            location=location,
            fov=fov,
        )
        camera.look_at(target=center)

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # close the unreal process
    xf_runner.close()

    logger.info(f'You can check the result with Unreal in: "{unreal_project}"')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
