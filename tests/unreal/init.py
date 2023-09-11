"""
>>> python -m tests.unreal.init_test
"""

from loguru import logger

from xrfeitoria.rpc import remote_unreal

from ..utils import __timer__, _init_unreal, setup_logger


@remote_unreal()
def test_unreal():
    import unreal  # fmt: skip
    unreal.log('test')


def init_test(debug: bool = False, dev: bool = False, background: bool = False):
    setup_logger(debug=debug)
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
