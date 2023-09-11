"""
>>> python -m samples.unreal.06_custom_usage

This is a script to demonstrate the custom use of xrfeitoria.
"""
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.rpc import remote_unreal

from ..config import unreal_exec, unreal_project
from ..utils import setup_logger

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/samples/unreal/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'blender.log'


@remote_unreal()
def add_cubes_in_unreal():
    """This function will be executed in unreal.

    Write your own unreal code here, and decorate it with `@remote_unreal`. The code of
    the functions decorated with `@remote_unreal` would be sent to unreal by RPC
    protocols.
    """
    import unreal

    # add 100 cubes marching in a 10x10 grid
    cube = unreal.load_asset('/Engine/BasicShapes/Cube')
    size = 0.2
    for i in range(10):
        for j in range(10):
            _location = unreal.Vector(i, j, size / 2)
            # convert from meters to centimeters
            _location *= 100.0
            _actor = unreal.EditorLevelLibrary().spawn_actor_from_object(object_to_use=cube, location=_location)
            _actor.set_actor_label(f'cube_{i:02d}_{j:02d}')
            _actor.set_actor_scale3d((size, size, size))


def main(debug=False, background=False):
    logger = setup_logger(debug=debug, log_path=log_path)
    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # The function `add_cubes_in_unreal` decorated with `@remote_unreal` will be executed in blender.
    add_cubes_in_unreal()

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    xf_runner.close()


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
