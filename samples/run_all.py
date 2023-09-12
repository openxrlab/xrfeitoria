import subprocess
from typing import Literal


def main(engine: Literal['unreal', 'blender'], debug: bool = False, background: bool = False):
    args = []
    if debug:
        args += ['--debug']
    if background:
        args += ['--background']

    scripts = [
        '01_add_shapes',
        '02_add_cameras',
        '03_basic_render',
        '04_staticmesh_render',
        '05_skeletalmesh_render',
        '06_custom_usage',
    ]
    for script in scripts:
        subprocess.check_call(['python', '-m', f'samples.{engine}.{script}'] + args)


if __name__ == '__main__':
    from .utils import parse_args

    args = parse_args()
    main(engine=args.engine, debug=args.debug, background=args.background)
