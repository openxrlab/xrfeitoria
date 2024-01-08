"""
>>> python -m tests.unreal.init_test
"""
import numpy as np
from loguru import logger

from xrfeitoria.data_structure.constants import xf_obj_name
from xrfeitoria.utils import setup_logger

from ..config import assets_path
from ..utils import __timer__, _init_unreal

bunny_obj = assets_path['bunny']
kc_fbx = assets_path['koupen_chan']
smpl_xl_fbx = assets_path['SMPL_XL']


def actor_test(debug: bool = False, background: bool = False):
    setup_logger(level='DEBUG' if debug else 'INFO')
    with _init_unreal(background=background) as xf_runner:
        with __timer__('import actor'):
            kc_path = xf_runner.utils.import_asset(path=kc_fbx)
            actor_kc = xf_runner.Actor.spawn_from_engine_path(kc_path, name='KoupenChan')
            assert actor_kc.name == 'KoupenChan', f'name not match, actor.name={actor_kc.name}'
            actor_kc.delete()

            actor_bunny = xf_runner.Actor.import_from_file(file_path=bunny_obj)
            actor_smpl_xl = xf_runner.Actor.import_from_file(file_path=smpl_xl_fbx)

            actor_bunny.delete()
            actor_smpl_xl.delete()

        with __timer__('spawn actor'):
            actor = xf_runner.Actor.spawn_from_engine_path(
                engine_path='/Engine/BasicShapes/Cube',
                name='Cube',
                location=(5, 3, 2),
                rotation=(30, 0, 0),
                scale=(0.1, 0.1, 0.1),
            )
            assert actor.name == 'Cube', f'name not match, actor.name={actor.name}'
            assert np.allclose(actor.location, (5, 3, 2)), f'location not match, actor.location={actor.location}'
            assert np.allclose(actor.rotation, (30, 0, 0)), f'rotation not match, actor.rotation={actor.rotation}'
            assert np.allclose(actor.scale, (0.1, 0.1, 0.1)), f'scale not match, actor.scale={actor.scale}'

        # set properties
        actor.location = (1, 2, 3)
        actor.rotation = (20, 30, 50)
        actor.scale = (2, 2, 2)
        assert np.allclose(actor.rotation, (20, 30, 50)), f'rotation not match, actor.rotation={actor.rotation}'
        assert np.allclose(actor.location, (1, 2, 3)), f'location not match, actor.location={actor.location}'
        assert np.allclose(actor.scale, (2, 2, 2)), f'scale not match, actor.scale={actor.scale}'

        # set/get transform
        actor.set_transform(location=(3, 4, 5), rotation=(10, 20, 30), scale=(3, 3, 3))
        loc, rot, scale = actor.get_transform()
        assert np.allclose(loc, (3, 4, 5)), f'location not match, loc={loc}'
        assert np.allclose(rot, (10, 20, 30)), f'rotation not match, rot={rot}'
        assert np.allclose(scale, (3, 3, 3)), f'scale not match, scale={scale}'

        actor.delete()

        with __timer__('spawn shape'):
            for _type in ['cube', 'sphere', 'cylinder', 'cone', 'plane']:
                actor = xf_runner.Shape.spawn(type=_type)
                assert actor.name == xf_obj_name.format(
                    obj_type=_type, obj_idx=1
                ), f'name not match, actor.name={actor.name}'
                actor.delete()

    logger.info('🎉 [bold green]actor tests passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args.add_argument('--background', '-b', action='store_true')
    args = args.parse_args()

    actor_test(debug=args.debug, background=args.background)
