"""
>>> python -m tests.unreal.init_test
"""

from pathlib import Path

from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.data_structure.models import SequenceTransformKey as SeqTransKey
from xrfeitoria.factory import XRFeitoriaUnreal
from xrfeitoria.utils import setup_logger

from ..config import assets_path
from ..utils import __timer__, _init_unreal, visualize_vertices

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/tests/unreal/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
seq_name = 'seq_test'

kc_fbx = assets_path['koupen_chan']


def new_seq(xf_runner: XRFeitoriaUnreal, level_path: str, seq_name: str):
    kc_path = xf_runner.utils.import_asset(path=kc_fbx)

    seq = xf_runner.sequence(level=level_path, seq_name=seq_name, seq_length=30, replace=True)
    seq.spawn_camera_with_keys(
        transform_keys=[
            SeqTransKey(frame=0, location=(0, 3, 1), rotation=(0, 0, -90), interpolation='AUTO'),
            SeqTransKey(frame=30, location=(-3, 2, 2), rotation=(0, 0, -45), interpolation='AUTO'),
        ],
        fov=90.0,
        camera_name='camera',
    )
    camera2 = xf_runner.Camera.spawn(camera_name='camera2')
    seq.use_camera_with_keys(
        camera=camera2,
        transform_keys=[
            SeqTransKey(frame=0, location=(-2, 0, 1), rotation=(0, 0, 0), interpolation='AUTO'),
            SeqTransKey(frame=30, location=(-5, 0, 1), rotation=(0, 0, 0), interpolation='AUTO'),
        ],
        fov=90.0,
    )
    seq.spawn_actor(
        actor_asset_path='/Engine/BasicShapes/Cube',
        actor_name='Actor',
        location=[3, 0, 0],
        rotation=[0, 0, 0],
        stencil_value=2,
    )
    seq.spawn_actor_with_keys(
        actor_asset_path='/Engine/BasicShapes/Cone',
        transform_keys=[
            SeqTransKey(frame=0, location=(-1, 0, 0), rotation=(0, 0, 0), interpolation='AUTO'),
            SeqTransKey(frame=30, location=(0, 3, 5), rotation=(0, 0, 360), interpolation='AUTO'),
        ],
        actor_name='Actor2',
        stencil_value=3,
    )
    seq.spawn_actor(
        actor_asset_path='/Engine/BasicShapes/Cylinder',
        location=[0, 0, 0],
        rotation=[0, 0, 0],
        stencil_value=4,
    )

    seq.spawn_actor_with_keys(
        actor_asset_path=kc_path,
        transform_keys=[
            SeqTransKey(
                frame=0, location=(0, 0, 0), rotation=(0, 0, 0), scale=(0.05, 0.05, 0.05), interpolation='AUTO'
            ),
            SeqTransKey(frame=5, location=(2, 0, 3), rotation=(0, 180, 0), interpolation='AUTO'),
            SeqTransKey(frame=10, location=(0, 3, 0), rotation=(180, 0, 0), interpolation='AUTO'),
            SeqTransKey(frame=15, location=(0, 0, 3), rotation=(0, 0, 180), interpolation='AUTO'),
            SeqTransKey(frame=20, location=(0, 0, 0), rotation=(0, 0, 0), interpolation='AUTO'),
        ],
        actor_name='KoupenChan',
        stencil_value=5,
    )

    seq.add_to_renderer(
        output_path=output_path,
        resolution=(1920, 1080),
        render_passes=[
            RenderPass('img', 'png'),
            RenderPass('mask', 'exr'),
        ],
        export_vertices=True,
        export_skeleton=True,
    )

    xf_runner.utils.save_current_level()

    seq.save()
    seq.close()


def sequence_test(debug: bool = False, background: bool = False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO')
    with _init_unreal(background=background) as xf_runner:
        xf_runner.Renderer.clear()

        default_level = '/Game/Levels/Default'
        level_template = '/Game/Levels/Playground'
        level_test = '/Game/Levels/SequenceTest'

        xf_runner.utils.open_level(default_level)
        xf_runner.utils.duplicate_asset(level_template, level_test, replace=True)

        with __timer__("create seq 'test'"):
            new_seq(xf_runner, level_path=level_test, seq_name=seq_name)
        with __timer__('render jobs'):
            xf_runner.Renderer.render_jobs()

    for frame_idx in range(0, 30, 5):
        visualize_vertices(
            camera_name='camera',
            actor_names=['KoupenChan'],
            seq_output_path=output_path / seq_name,
            frame_idx=frame_idx,
        )

    logger.info('🎉 [bold green]sequence tests passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args.add_argument('--background', '-b', action='store_true')
    args = args.parse_args()

    sequence_test(debug=args.debug, background=args.background)
