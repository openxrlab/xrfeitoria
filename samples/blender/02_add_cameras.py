"""
>>> python -m samples.blender.02_add_cameras

This is a script to add cameras in blender.
"""
import math
from pathlib import Path

import xrfeitoria as xf

from ..config import blender_exec
from ..utils import setup_logger

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/samples/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'blender.log'
output_blend_file = output_path / 'source.blend'


def main(debug=False, background=False):
    logger = setup_logger(debug=debug, log_path=log_path)

    # Open blender
    xf_runner = xf.init_blender(exec_path=blender_exec, background=background, new_process=True)

    # Add 32 circled cameras around the center
    center = (1, 2, 3)
    distance = 1
    fov = 90

    for i in range(32):
        azimuth = 360 / 32 * i
        azimuth_radians = math.radians(azimuth)

        x = distance * math.cos(azimuth_radians) + center[0]
        y = distance * math.sin(azimuth_radians) + center[1]
        z = 0.0 + center[2]
        location = (x, y, z)

        camera = xf_runner.Camera.spawn(
            camera_name=f'camera_{i}',
            location=location,
            fov=fov,
        )
        camera.look_at(target=center)

    # Save the blender file to the current directory.
    xf_runner.utils.save_blend(save_path=output_blend_file)

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # close the blender process
    xf_runner.close()

    logger.info(f'You can check the result with Blender in: "{output_blend_file}"')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
