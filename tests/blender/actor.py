"""
python -m tests.blender.actor
"""
from pathlib import Path

import numpy as np
from loguru import logger

from ..utils import __timer__, _init_blender, set_logger

root = Path(__file__).parent.resolve()


def actor_test(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with _init_blender(background=background) as xf_runner:
        with __timer__("import_actor"):
            actor = xf_runner.Actor.import_actor_from_file(
                name="new_actor",
                path=(root.parent / "assets" / "cube.fbx").as_posix(),
                location=(0, 0, 0),
                rotation=(90, 0, 0),
                scale=(2, 1, 1),
            )
            assert np.allclose(actor.location, (0, 0, 0)), f"location: {actor.location}"
            assert np.allclose(actor.rotation, (90, 0, 0)), f"rotation: {actor.rotation}"
            assert np.allclose(actor.scale, (2, 1, 1)), f"scale: {actor.scale}"

        with __timer__("spawn_actor"):
            cube = xf_runner.Mesh.spawn_mesh(name="my cube", mesh_type="cube")
            cube.location = (3, 0, 0)
            assert np.allclose(cube.location, (3, 0, 0)), f"location: {cube.location}"

            ico_sphere = xf_runner.Mesh.spawn_mesh(name="ico sphere", mesh_type="ico_sphere", subdivisions=4)
            ico_sphere.rotation = (40, 0, 0)
            assert np.allclose(ico_sphere.rotation, (40, 0, 0)), f"rotation: {ico_sphere.rotation}"

            uv_sphere = xf_runner.Mesh.spawn_mesh(name="uv sphere", mesh_type="uv_sphere", segments=32, ring_count=32)
            uv_sphere.scale = (3, 3, 3)
            assert np.allclose(uv_sphere.scale, (3, 3, 3)), f"scale: {uv_sphere.scale}"

            plane = xf_runner.Mesh.spawn_mesh(name="plane", mesh_type="plane", size=5)
            plane.set_transform(location=(0, 0, 1), rotation=(0, 0, 90), scale=(1, 3, 1))
            assert np.allclose(plane.location, (0, 0, 1)), f"location: {plane.location}"
            assert np.allclose(plane.rotation, (0, 0, 90)), f"rotation: {plane.rotation}"
            assert np.allclose(plane.scale, (1, 3, 1)), f"scale: {plane.scale}"

            cylinder = xf_runner.Mesh.spawn_mesh(
                name="cylinder",
                mesh_type="cylinder",
                location=(0, 0, 2),
                rotation=(0, 150, 0),
                scale=(3, 2, 1),
                vertices=16,
            )
            location, rotation, scale = cylinder.get_transform()
            assert np.allclose(location, (0, 0, 2)), f"location: {location}"
            assert np.allclose(rotation, (0, 150, 0)), f"rotation: {rotation}"
            assert np.allclose(scale, (3, 2, 1)), f"scale: {scale}"

            # cone = xf_runner.Actor.spawn_mesh(name="cone", mesh_type="cone", radius1=2, radius2=3, vertices=16)

    logger.info("🎉 actor tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    actor_test(debug=args.debug, background=args.background)
