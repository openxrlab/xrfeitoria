"""
python -m tests.blender.camera
"""
import numpy as np
from loguru import logger

from ..utils import __timer__, _init_blender, set_logger


def camera_test(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with _init_blender(background=background) as xf_runner:
        with __timer__("spawn camera"):
            ## test spawn camera
            cam = xf_runner.Camera.spawn_camera(
                name="new cam",
                location=(5, 6, 7),
                rotation=(30, 0, 0),
                fov=20,
            )
            assert np.allclose(cam.location, (5, 6, 7)), f"❌ cam.location={cam.location} wrong"
            assert np.allclose(cam.rotation, (30, 0, 0)), f"❌ cam.rotation={cam.rotation} wrong"

        with __timer__("move camera"):
            ## test camera location & rotation setters
            cam.location = (2, 3, 4)
            cam.rotation = (45, 25, 135)
            assert np.allclose(cam.location, (2, 3, 4)), "❌ cam.location wrong"
            assert np.allclose(cam.rotation, (45, 25, 135)), "❌ cam.rotation wrong"

        with __timer__("get camera"):
            cam = xf_runner.Camera("new cam")

        with __timer__("delete camera"):
            cam.delete()

    logger.info("🎉 camera tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    camera_test(debug=args.debug, background=args.background)
