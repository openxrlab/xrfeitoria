""" 
python -m tests.blender.init
"""

from loguru import logger

from ..utils import __timer__, _init_blender, set_logger, test_blender


def init_test(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with __timer__("init_blender"):
        with _init_blender(background=background) as xf_runner:
            test_blender()

    logger.info("🎉 init tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    init_test(debug=args.debug, background=args.background)
