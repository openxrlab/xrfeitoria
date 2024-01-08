"""
>>> python -m tests.blender.camera
"""
from pathlib import Path

import numpy as np

from xrfeitoria.data_structure.constants import xf_obj_name
from xrfeitoria.utils import setup_logger

from ..utils import __timer__, _init_blender

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/tests/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')


def camera_test(debug: bool = False, background: bool = False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO')
    with _init_blender(background=background) as xf_runner:
        with __timer__('spawn camera'):
            ## test spawn camera
            cam0 = xf_runner.Camera.spawn()
            assert cam0.name == xf_obj_name.format(obj_type='camera', obj_idx=1), f'❌ cam1.name={cam0.name} wrong'
            cam0.delete()

            cam = xf_runner.Camera.spawn(
                camera_name='new cam',
                location=(5, 6, 7),
                rotation=(30, 0, 0),
                fov=20,
            )
            assert cam.name == 'new cam', f'❌ cam.name={cam.name} wrong'
            assert np.allclose(cam.location, (5, 6, 7)), f'❌ cam.location={cam.location} wrong'
            assert np.allclose(cam.rotation, (30, 0, 0)), f'❌ cam.rotation={cam.rotation} wrong'

        with __timer__('move camera'):
            ## test camera location & rotation setters
            cam.location = (2, 3, 4)
            cam.rotation = (45, 25, 135)
            assert np.allclose(cam.location, (2, 3, 4)), '❌ cam.location wrong'
            assert np.allclose(cam.rotation, (45, 25, 135)), '❌ cam.rotation wrong'

        with __timer__('get camera'):
            cam = xf_runner.Camera('new cam')
            assert np.allclose(cam.location, (2, 3, 4)), '❌ get cam wrong'

        with __timer__('dump camera params'):
            param_json = output_path / 'camera_params.json'
            cam.dump_params(param_json)
            assert param_json.exists(), '❌ dump camera params failed'
            # param_json.unlink()
            # logger.info('🗑️ delete camera params file')

        with __timer__('delete camera'):
            cam.delete()

    logger.info('🎉 [bold green]camera tests passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args.add_argument('--background', '-b', action='store_true')
    args = args.parse_args()

    camera_test(debug=args.debug, background=args.background)
