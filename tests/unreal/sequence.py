""" 
python -m tests.unreal.init_test
"""


from functools import partial

from loguru import logger

from xrfeitoria import RenderPass, XRFeitoriaUnreal
from xrfeitoria import SequenceTransformKey as SeqTransKey

from ..utils import __timer__, _init_unreal, set_logger


def create_seq(xf_runner: XRFeitoriaUnreal, map_path: str, seq_name: str):
    with xf_runner.new_seq(map_path=map_path, seq_name=seq_name, seq_length=30, replace=True) as seq:
        seq.control_camera_with_keys(
            transform_keys=SeqTransKey(
                frame=0, location=(200, -400, 100), rotation=(0, 0, 90), interpolation="CONSTANT"
            ),
            fov=120.0,
            camera_name="CineCameraActor",
        )
        seq.control_actor(
            actor_name="Cube",
            location=(0, 0, 200),
            rotation=(0, 0, 180),
            actor_stencil_value=1,
        )

        seq.spawn_camera(location=(-500, 0, 100), rotation=(0, 0, 0), fov=90.0, camera_name="Camera")
        seq.spawn_camera_with_keys(
            transform_keys=[
                SeqTransKey(frame=0, location=(-200, 0, 100), rotation=(0, 0, 0), interpolation="CUBIC"),
                SeqTransKey(frame=30, location=(-500, 0, 100), rotation=(0, 0, 0), interpolation="CUBIC"),
            ],
            fov=90.0,
            camera_name="Camera2",
        )
        seq.spawn_actor(
            actor_asset_path='/Game/StarterContent/Props/SM_Couch',
            actor_name="Actor",
            location=[300, 0, 0],
            rotation=[0, 0, 0],
            actor_stencil_value=2,
        )
        seq.spawn_actor_with_keys(
            actor_asset_path='/Game/StarterContent/Props/SM_Chair',
            transform_keys=[
                SeqTransKey(frame=0, location=(-100, 0, 0), rotation=(0, 0, 0), interpolation="CUBIC"),
                SeqTransKey(frame=30, location=(0, 0, 0), rotation=(0, 0, 360), interpolation="CUBIC"),
            ],
            actor_name="Actor2",
            actor_stencil_value=3,
        )
        # seq.show()
        # xf_runner.Renderer.add_job(
        #     map_path=seq.get_map_path(),
        #     sequence_path=seq.get_seq_path(),
        #     output_path="D:/tmp",
        #     resolution=(1920, 1080),
        #     render_passes=[
        #         RenderPass("img", "png"),
        #         RenderPass("mask", "exr"),
        #     ],
        # )


def open_seq(xf_runner: XRFeitoriaUnreal, map_path: str, seq_name: str):
    with xf_runner.open_seq(map_path=map_path, seq_name=seq_name) as seq:
        seq.show()
        # xf_runner.Renderer.add_job(
        #     map_path=seq.get_map_path(),
        #     sequence_path=seq.get_seq_path(),
        #     output_path="D:/tmp",
        #     resolution=(1920, 1080),
        #     render_passes=[
        #         RenderPass("img", "png"),
        #         RenderPass("mask", "exr"),
        #     ],
        # )


def add_job_in_batch(xf_runner: XRFeitoriaUnreal, jobs: list[dict[str, str]]):
    _add_job = partial(
        xf_runner.Renderer.add_job,
        map_path="/Game/NewMap",
        output_path="D:/tmp",
        resolution=(1920, 1080),
        render_passes=[
            RenderPass("img", "png"),
            RenderPass("mask", "exr"),
        ],
    )
    for job in jobs:
        map_path = job["map_path"]
        seq_name = job["seq_name"]
        _add_job(sequence_path=xf_runner.get_seq_path(map_path=map_path, seq_name=seq_name))


def sequence_test(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with _init_unreal(background=background) as xf_runner:
        with __timer__("create seq 'test'"):
            create_seq(xf_runner, map_path="/Game/NewMap", seq_name="test")
        with __timer__("create seq 'test2'"):
            create_seq(xf_runner, map_path="/Game/NewMap", seq_name="test2")
        with __timer__("open seq 'test'"):
            open_seq(xf_runner, map_path="/Game/NewMap", seq_name="test")
        with __timer__("add jobs to render queue"):
            xf_runner.Renderer.clear()
            add_job_in_batch(
                xf_runner,
                jobs=[
                    {"map_path": "/Game/NewMap", "seq_name": "test"},
                    {"map_path": "/Game/NewMap", "seq_name": "test2"},
                ],
            )
        with __timer__("render jobs"):
            xf_runner.Renderer.render_jobs()

    logger.info("🎉 sequence tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    sequence_test(debug=args.debug, background=args.background)
