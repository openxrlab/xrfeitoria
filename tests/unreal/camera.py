"""
>>> python -m tests.unreal.init_test
"""

import numpy as np

from xrfeitoria.data_structure.constants import xf_obj_name
from xrfeitoria.utils import setup_logger

from ..utils import __timer__, _init_unreal


def camera_test(debug: bool = False, background: bool = False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO')
    with _init_unreal(background=background) as xf_runner:
        with __timer__('spawn camera'):
            camera0 = xf_runner.Camera.spawn()
            assert camera0.name == xf_obj_name.format(
                obj_type='camera', obj_idx=1
            ), f'name not match, camera0.name={camera0.name}'
            camera0.delete()

            camera = xf_runner.Camera.spawn(
                camera_name='new cam',
                location=(5, 3, 2),
                rotation=(30, 0, 0),
                fov=90.0,
            )
            assert camera.name == 'new cam', f'name not match, camera.name={camera.name}'
            assert np.allclose(camera.location, (5, 3, 2)), f'location not match, camera.location={camera.location}'
            assert np.allclose(camera.rotation, (30, 0, 0)), f'rotation not match, camera.rotation={camera.rotation}'
            assert np.allclose(camera.fov, 90.0), f'fov not match, camera.fov={camera.fov}'

        with __timer__('set location'):
            camera.location = (1, 2, 3)
            assert np.allclose(camera.location, (1, 2, 3)), f'location not match, camera.location={camera.location}'

        with __timer__('set rotation'):
            camera.rotation = (20, 30, 50)
            assert np.allclose(camera.rotation, (20, 30, 50)), f'rotation not match, camera.rotation={camera.rotation}'

        with __timer__('set fov'):
            camera.fov = 60.0
            assert np.allclose(camera.fov, 60.0), f'fov not match, camera.fov={camera.fov}'

        with __timer__('delete camera'):
            camera.delete()

    logger.info('🎉 [bold green]camera tests passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args.add_argument('--background', '-b', action='store_true')
    args = args.parse_args()

    camera_test(debug=args.debug, background=args.background)
