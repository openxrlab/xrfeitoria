""" 
python -m tests.unreal.init_test
"""
import numpy as np
from loguru import logger

from ..utils import __timer__, _init_unreal, set_logger


def actor_test(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with _init_unreal(background=background) as xf_runner:
        with __timer__("spawn actor"):
            actor = xf_runner.Actor.spawn_from_engine_path(
                engine_path='/Game/StarterContent/Props/SM_Couch',
                name="SM_Couch3",
                location=(500, 300, 200),
                rotation=(30, 0, 0),
                scale=(0.1, 0.1, 0.1),
            )
            assert np.allclose(actor.location, (500, 300, 200)), f"location not match, actor.location={actor.location}"
            assert np.allclose(actor.rotation, (30, 0, 0)), f"rotation not match, actor.rotation={actor.rotation}"
            assert np.allclose(actor.scale, (0.1, 0.1, 0.1)), f"scale not match, actor.scale={actor.scale}"

        with __timer__("set location"):
            actor.location = (100, 200, 300)
            assert np.allclose(actor.location, (100, 200, 300)), f"location not match, actor.location={actor.location}"

        with __timer__("set rotation"):
            actor.rotation = (20, 30, 50)
            assert np.allclose(actor.rotation, (20, 30, 50)), f"rotation not match, actor.rotation={actor.rotation}"

        with __timer__("set scale"):
            actor.scale = (2, 2, 2)
            assert np.allclose(actor.scale, (2, 2, 2)), f"scale not match, actor.scale={actor.scale}"

        with __timer__("delete actor"):
            actor.delete()

    logger.info("🎉 actor tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    actor_test(debug=args.debug, background=args.background)
