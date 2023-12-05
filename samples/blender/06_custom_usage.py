"""
>>> python -m samples.blender.06_custom_usage

This is a script to demonstrate the custom use of xrfeitoria.
"""
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.rpc import remote_blender
from xrfeitoria.utils import setup_logger

from ..config import blender_exec

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/samples/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'blender.log'
output_blend_file = output_path / 'source.blend'


@remote_blender()
def add_cubes_in_blender():
    """This function will be executed in blender.

    Write your own blender code here, and decorate it with `@remote_blender`. The code
    of the functions decorated with `@remote_blender` would be sent to blender by RPC
    protocols.
    """
    import bpy

    # add 100 cubes marching in a 10x10 grid
    for i in range(10):
        for j in range(10):
            bpy.ops.mesh.primitive_cube_add(size=0.1, location=(i, j, 0))


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)

    xf_runner = xf.init_blender(exec_path=blender_exec, background=background, new_process=True)
    # The function `add_cubes_in_blender` decorated with `@remote_blender` will be executed in blender.
    add_cubes_in_blender()

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
