"""
python -m tests.blender.camera
"""
import math
from pathlib import Path

from loguru import logger

from xrfeitoria import RenderPass, XRFetoriaBlender
from xrfeitoria import SequenceTransformKey as SeqTransKey

from ..utils import __timer__, _init_blender, set_logger

root = Path(__file__).parent.resolve()
hdr_map_path = (root.parent / "assets" / "white-background.hdr").as_posix()
# actor_path = (root.parent / "assets" / "people.fbx").as_posix()
# anim_path = (root.parent / "assets" / "anim.fbx").as_posix()


def level_test(xf_runner: XRFetoriaBlender):
    cube = xf_runner.Mesh.spawn_cube(name="cube")
    cube.location = (4, 5, 6)
    cube.rotation = (30, 50, 60)

    actor1 = xf_runner.Actor.import_actor_from_file(
        name="actor1",
        path=str(root.parent / "assets" / "36_18_armature.fbx"),
        stencil_value=255,
    )
    actor1.setup_animation(
        anim_asset_path=str(root.parent / "assets" / "36_18_motion.blend"),
        action_name="ArmatureAction",
    )
    actor2 = xf_runner.Actor.import_actor_from_file(
        name="actor2",
        path=str(root.parent / "assets" / "36_18_armature.fbx"),
        stencil_value=255,
    )
    actor2.setup_animation(anim_asset_path=str(root.parent / "assets" / "mo_json.json"))
    cam_level = xf_runner.Camera.spawn_camera("level_camera")
    cam_level.location = (-10, 0, 0)
    cam_level.rotation = (90, 0, -90)
    cam_level.fov = 39.6
    return cam_level


def sequence_test(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with _init_blender(background=background, cleanup=True, replace_plugin=True) as xf_runner:
        with __timer__("level test"):
            cam_level = level_test(xf_runner)

        with __timer__("sequence test"):
            with xf_runner.new_seq(
                seq_name="Seq_1", seq_length=60, seq_fps=60, hdr_map_path=hdr_map_path, replace=True
            ) as seq:
                cam_level.active = True

                ico_sphere = seq.spawn_mesh_with_keys(
                    mesh_name="ico_sphere",
                    mesh_type="ico_sphere",
                    stencil_value=128,
                    subdivisions=3,
                    transform_keys=[
                        SeqTransKey(frame=0, location=(-2, 0, 1), rotation=(0, 0, 0), interpolation="BEZIER"),
                        SeqTransKey(frame=30, location=(-5, 3, 4), rotation=(0, 0, 0), interpolation="BEZIER"),
                        SeqTransKey(
                            frame=60,
                            location=(3, 4, -5),
                            rotation=(math.radians(40), math.radians(30), math.radians(20)),
                            interpolation="BEZIER",
                        ),
                    ],
                )
                ico_sphere.scale = (2, 0.8, 1.5)
                ico_sphere.location = (-5, -2, 3)

                actor3 = seq.spawn_actor(
                    "actor3",
                    actor_asset_path=str(root.parent / "assets" / "people.fbx"),
                )
                actor3.setup_animation(
                    anim_asset_path=str(
                        root.parent
                        / "assets"
                        / "Subject_80_F_19-Sens_people_3767-frame_interval_1-frame_start_21-frame_end_82-fps_30.fbx"
                    )
                )
                actor3.scale = (0.01, 0.01, 0.01)

                xf_runner.Renderer.add_job(
                    seq_name=seq.name,
                    output_path=str(root.parent / "output"),
                    render_passes=[
                        {
                            "render_layer": "img",
                            "image_format": "png",
                        },
                        {
                            "render_layer": "mask",
                            "image_format": "png",
                        },
                    ],
                    resolution=[512, 512],
                    render_engine="CYCLES",
                    render_samples=128,
                    transparent_background=False,
                    arrange_file_structure=True,
                )

        with __timer__("render"):
            xf_runner.Renderer.render_jobs(use_gpu=True)

        with __timer__("save_blend"):
            xf_runner.utils.save_blend(
                save_path=str(root.parent / "output" / "test.blend"),
            )

    logger.info("🎉 sequence tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    sequence_test(debug=args.debug, background=args.background)
