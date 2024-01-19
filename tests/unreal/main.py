"""
>>> python -m tests.unreal.main
"""
from pathlib import Path

from xrfeitoria.utils import setup_logger

from ..utils import _init_unreal
from .actor import actor_test
from .camera import camera_test
from .init import init_test
from .sequence import sequence_test

root = Path(__file__).parent


def main(debug: bool = False, background: bool = False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=root / 'unreal.log')

    with _init_unreal(background=background, dev_plugin=True) as xf_runner:
        init_test(debug=debug, background=background)
        actor_test(debug=debug, background=background)
        camera_test(debug=debug, background=background)
        sequence_test(debug=debug, background=background)

    logger.info('🎉 [bold green]All tests passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args = args.parse_args()

    main(debug=args.debug)
