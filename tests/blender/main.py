"""
>>> python -m tests.blender.main
"""
from pathlib import Path

from xrfeitoria.utils import setup_logger

from ..utils import _init_blender
from .actor import actor_test
from .camera import camera_test
from .init import init_test
from .level import level_test
from .sequence import sequence_test

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/tests/blender'
output_path = root / 'output' / Path(__file__).parent.relative_to(root)


def main(debug: bool = False, background: bool = False):
    logger = setup_logger(debug=debug, log_path=output_path / 'blender.log')
    with _init_blender(background=background) as xf_runner:
        init_test(debug=debug)
        actor_test(debug=debug)
        camera_test(debug=debug)
        sequence_test(debug=debug)

    level_test(debug=debug, background=background)

    logger.info('🎉 [bold green]All tests passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args.add_argument('--background', '-b', action='store_true')
    args = args.parse_args()

    main(debug=args.debug, background=args.background)
