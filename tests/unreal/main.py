from loguru import logger

from .init import init_test


def main(debug: bool = False, background: bool = False):
    init_test(debug=debug)

    logger.info("🎉 All tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args = args.parse_args()

    main(debug=args.debug)
