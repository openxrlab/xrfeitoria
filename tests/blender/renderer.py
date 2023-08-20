"""
python -m tests.blender.renderer
"""
from pathlib import Path

from loguru import logger

import xrfeitoria as xf

from ..utils import __timer__, _init_blender, set_logger

root = Path(__file__).parent.resolve()


def renderer_test(debug: bool = False, background: bool = False):
    set_logger(debug=debug)
    with _init_blender(background=background) as xf_runner:
        with __timer__("add render pass via `RenderPass`"):
            render_passes = [
                xf.RenderPass("img", "jpg"),
                xf.RenderPass("mask", "png"),
                xf.RenderPass("depth", "exr"),
                xf.RenderPass("denoising_depth", "exr"),
                xf.RenderPass("flow", "exr"),
                xf.RenderPass("normal", "png"),
                xf.RenderPass("diffuse", "png"),
            ]
            xf_runner.Renderer.add_job(
                # seq_name=seq.name,
                output_path=str(root.parent / "output"),
                render_passes=render_passes,
                resolution=[64, 64],
                render_engine="CYCLES",
                render_samples=128,
                transparent_background=False,
                arrange_file_structure=True,
            )
        # with __timer__("add render pass via `dict`"):
        #     render_passes = [
        #         {
        #             "render_layer": "img",
        #             "image_format": "png",
        #         },
        #         {
        #             "render_layer": "mask",
        #             "image_format": "exr",
        #         },
        #     ]
        #     renderer = xf_runner.Renderer(
        #         output_path=(root / "__output").as_posix(),
        #         resolution=(1920, 1080),
        #         render_passes=render_passes,
        #     )

    logger.info("🎉 renderer tests passed!")


if __name__ == "__main__":
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true")
    args.add_argument("--background", "-b", action="store_true")
    args = args.parse_args()

    renderer_test(debug=args.debug, background=args.background)
