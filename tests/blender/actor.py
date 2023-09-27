"""
>>> python -m tests.blender.actor
"""
from pathlib import Path

import numpy as np

from xrfeitoria.data_structure.constants import xf_obj_name
from xrfeitoria.data_structure.models import SequenceTransformKey as SeqTransKey

from ..config import assets_path
from ..utils import __timer__, _init_blender, setup_logger

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/tests/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
bunny_obj = assets_path['bunny']


def actor_test(debug: bool = False, background: bool = False):
    logger = setup_logger(debug=debug)
    with _init_blender(background=background, replace_plugin=True, dev_plugin=True) as xf_runner:
        with __timer__('import_actor'):
            actor = xf_runner.Actor.import_from_file(
                actor_name='bunny',
                file_path=bunny_obj,
                location=(0, 0, 0),
                rotation=(90, 0, 0),
                scale=(2, 1, 1),
            )
            # test properties
            assert actor.name == 'bunny', f'name not match, actor.name={actor.name}'
            assert np.allclose(actor.location, (0, 0, 0)), f'location: {actor.location}'
            assert np.allclose(actor.rotation, (90, 0, 0)), f'rotation: {actor.rotation}'
            assert np.allclose(actor.scale, (2, 1, 1)), f'scale: {actor.scale}'

            # test set properties
            actor.location = (3, 0, 0)
            actor.rotation = (40, 0, 0)
            actor.scale = (3, 3, 3)
            assert np.allclose(actor.location, (3, 0, 0)), f'location: {actor.location}'
            assert np.allclose(actor.rotation, (40, 0, 0)), f'rotation: {actor.rotation}'
            assert np.allclose(actor.scale, (3, 3, 3)), f'scale: {actor.scale}'

            # test functions
            # test get_transform/set_transform
            actor.set_transform(location=(0, 0, 1), rotation=(0, 0, 90), scale=(1, 3, 1))
            assert np.allclose(actor.location, (0, 0, 1)), f'location: {actor.location}'
            assert np.allclose(actor.rotation, (0, 0, 90)), f'rotation: {actor.rotation}'
            assert np.allclose(actor.scale, (1, 3, 1)), f'scale: {actor.scale}'

            location, rotation, scale = actor.get_transform()
            assert np.allclose(location, (0, 0, 1)), f'location: {location}'
            assert np.allclose(rotation, (0, 0, 90)), f'rotation: {rotation}'
            assert np.allclose(scale, (1, 3, 1)), f'scale: {scale}'

            # test set_transform_keys
            xf_runner.ObjectUtils.set_transform_keys(
                name=actor.name,
                transform_keys=[
                    SeqTransKey(frame=0, location=(-1, 0, 1.8), rotation=(0, 0, 0), interpolation='AUTO'),
                    SeqTransKey(frame=30, location=(-1, 0, -1.1), rotation=(0, 0, 0), interpolation='AUTO'),
                    SeqTransKey(frame=40, location=(1, 0, -1.1), rotation=(40, 30, 20), interpolation='AUTO'),
                ],
            )
            if not xf_runner.utils.is_background_mode():
                xf_runner.utils.set_frame_current(0)
                assert np.allclose(actor.location, (-1, 0, 1.8)), f'location: {actor.location}'
                assert np.allclose(actor.rotation, (0, 0, 0)), f'rotation: {actor.rotation}'
                xf_runner.utils.set_frame_current(30)
                assert np.allclose(actor.location, (-1, 0, -1.1)), f'location: {actor.location}'
                assert np.allclose(actor.rotation, (0, 0, 0)), f'rotation: {actor.rotation}'
            xf_runner.utils.set_frame_current(40)
            assert np.allclose(actor.location, (1, 0, -1.1)), f'location: {actor.location}'
            assert np.allclose(actor.rotation, (40, 30, 20)), f'rotation: {actor.rotation}'
            xf_runner.utils.set_frame_current(0)

            # test set origin
            logger.info(f':rabbit: actor location: {actor.location}')
            actor.set_origin_to_center()
            logger.info(f':rabbit: actor location after set origin: {actor.location}')
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
