"""
>>> python -m samples.blender.01_add_shapes

This is a script to add shapes in blender.
"""
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.utils import setup_logger

from ..config import blender_exec

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/samples/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'blender.log'
output_blend_file = output_path / 'source.blend'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)

    # The blender will start in a separate process in RPC Server mode automatically,
    # and close when calling `xf_runner.close()`.
    xf_runner = xf.init_blender(exec_path=blender_exec, background=background, new_process=True)

    # add 4 types of shapes
    for i in range(4):
        xf_runner.Shape.spawn_cube(name=f'cube_{i}', location=(0, i, 0), size=0.2)
    for i in range(4):
        xf_runner.Shape.spawn_sphere(name=f'sphere_{i}', location=(1, i, 0), radius=0.1)
    for i in range(4):
        xf_runner.Shape.spawn_cylinder(name=f'cylinder_{i}', location=(2, i, 0), radius=0.1, depth=0.2)
    for i in range(4):
        xf_runner.Shape.spawn_cone(name=f'cone_{i}', location=(3, i, 0), radius1=0.1, depth=0.2)

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
