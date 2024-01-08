"""
>>> python -m tests.unreal.init_test
"""

from xrfeitoria.rpc import remote_unreal
from xrfeitoria.utils import setup_logger

from ..utils import __timer__, _init_unreal


@remote_unreal()
def test_unreal():
    import unreal  # fmt: skip
    unreal.log('test')


def init_test(debug: bool = False, dev: bool = False, background: bool = False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO')
    with __timer__('init unreal'):
        with _init_unreal(dev_plugin=dev, background=background) as xf_runner:
            test_unreal()

    logger.info('🎉 [bold green]init tests passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args.add_argument('--dev', action='store_true')
    args.add_argument('--background', '-b', action='store_true')
    args = args.parse_args()

    init_test(debug=args.debug, dev=args.dev, background=args.background)
