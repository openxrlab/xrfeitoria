""" 
python -m tests.blender.main
"""
from loguru import logger

from ..utils import _init_blender, set_logger
from .actor import actor_test
from .camera import camera_test
from .init import init_test
from .renderer import renderer_test


def main(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with _init_blender(background=background) as xf_runner:
        init_test(debug=debug)
        actor_test(debug=debug)
        camera_test(debug=debug)
        renderer_test(debug=debug)

    logger.info("🎉 All tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    main(debug=args.debug, background=args.background)
