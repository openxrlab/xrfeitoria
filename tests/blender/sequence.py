"""
>>> python -m tests.blender.sequence
"""
from pathlib import Path

import numpy as np
from loguru import logger

from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.data_structure.models import SequenceTransformKey as SeqTransKey
from xrfeitoria.factory import XRFeitoriaBlender
from xrfeitoria.utils import setup_logger

from ..config import assets_path
from ..utils import __timer__, _init_blender

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/tests/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')

# define testing assets
hdr_map_path = assets_path['hdr_sample']
bunny_obj_path = assets_path['bunny']
actor_path = assets_path['SMPL_XL']
motion_path = assets_path['motion_1']


def seq_actor(xf_runner: XRFeitoriaBlender, seq_name: str = 'seq_actor'):
    xf_runner.utils.set_hdr_map(hdr_map_path=hdr_map_path)

    camera_level = xf_runner.Camera.spawn(location=(0, 10, 0))
    camera_level.look_at(target=(0, 0, 0))

    with xf_runner.Sequence.new(seq_name=seq_name, seq_length=2) as seq:
        seq.use_camera(camera_level)
        camera = seq.spawn_camera(camera_name='camera', location=(-10, 0, 0), rotation=(90, 0, -90), fov=39.6)

        assert np.allclose(camera.location, (-10, 0, 0)), f'❌ cam.location={camera.location} wrong'
        assert np.allclose(camera.rotation, (90, 0, -90)), f'❌ cam.rotation={camera.rotation} wrong'
        assert np.allclose(camera.fov, 39.6), f'❌ cam.fov={camera.fov} wrong'

        camera1 = seq.spawn_camera_with_keys(
            transform_keys=[
                SeqTransKey(frame=0, location=(-1, 0, 1.8), rotation=(0, 0, 0), interpolation='AUTO'),
                SeqTransKey(frame=30, location=(-1, 0, -1.1), rotation=(0, 0, 0), interpolation='AUTO'),
                SeqTransKey(frame=40, location=(1, 0, -1.1), rotation=(40, 30, 20), interpolation='AUTO'),
            ],
        )
        # assert np.allclose(camera1.location, (-1, 0, 1.8)), f'❌ cam.location={camera1.location} wrong'
        # assert np.allclose(camera1.rotation, (0, 0, 0)), f'❌ cam.rotation={camera1.rotation} wrong'

        actor1 = seq.import_actor(file_path=actor_path, stencil_value=128)
        actor1.setup_animation(animation_path=motion_path)
        actor2 = seq.import_actor_with_keys(
            file_path=actor_path,
            transform_keys=[
                SeqTransKey(
                    frame=0, location=(-1, 0, 1.8), rotation=(0, 0, 0), scale=(0.01, 0.01, 0.01), interpolation='AUTO'
                ),
                SeqTransKey(frame=30, location=(-1, 0, -1.1), rotation=(0, 0, 0), interpolation='AUTO'),
                SeqTransKey(frame=40, location=(1, 0, -1.1), rotation=(40, 30, 20), interpolation='AUTO'),
            ],
            stencil_value=255,
        )

        # get keys range
        keys_range = xf_runner.utils.get_keys_range()
        logger.info(f'keys_range={keys_range}')

        logger.info('Override frame range to [0, 2] for testing')
        xf_runner.utils.set_frame_range(start=0, end=2)

        seq.add_to_renderer(
            output_path=output_path / f'{seq.name}',
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'png'),
            ],
            resolution=[128, 128],
            render_engine='CYCLES',
            render_samples=1,
            transparent_background=False,
            arrange_file_structure=True,
        )


def seq_shape(xf_runner: XRFeitoriaBlender, seq_name='seq_shape'):
    with xf_runner.Sequence.new(seq_name=seq_name, seq_length=6) as seq:
        camera = seq.spawn_camera(location=(-10, 0, 0), rotation=(90, 0, -90), fov=39.6)

        xf_runner.utils.set_frame_current(frame=3)

        cube = seq.spawn_shape(type='cube', size=1.0, stencil_value=128)
        cube1 = seq.spawn_shape_with_keys(
            type='cube',
            transform_keys=[
                SeqTransKey(
                    frame=0,
                    location=(-1, 0, 1.8),
                    rotation=(0, 0, 0),
                    interpolation='AUTO',
                ),
                SeqTransKey(
                    frame=3,
                    location=(-1, 0, -1.1),
                    rotation=(0, 0, 0),
                    interpolation='AUTO',
                ),
                SeqTransKey(
                    frame=6,
                    location=(1, 0, -1.1),
                    rotation=(40, 30, 20),
                    interpolation='AUTO',
                ),
            ],
            size=0.1,
            stencil_value=255,
        )
        seq.add_to_renderer(
            output_path=output_path / f'{seq.name}',
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'exr'),
            ],
            resolution=[128, 128],
            render_engine='CYCLES',
            render_samples=1,
            transparent_background=False,
            arrange_file_structure=True,
        )


def sequence_test(debug=False, background=False):
    setup_logger(level='DEBUG' if debug else 'INFO')
    with _init_blender(background=background) as xf_runner:
        with __timer__('seq_actor'):
            seq_actor(xf_runner, seq_name='seq_actor')

        with __timer__('seq_shape'):
            seq_shape(xf_runner, seq_name='seq_shape')

        # save blend
        blend_file = output_path / 'source.blend'
        xf_runner.utils.save_blend(save_path=blend_file)

        with __timer__('render'):
            xf_runner.render()

    logger.info('🎉 [bold green]sequence & render tests passed!')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    sequence_test(debug=args.debug, background=args.background)
