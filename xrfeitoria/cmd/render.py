"""Render a mesh with blender to output_path.

>>> xf-render --help
>>> xf-render {mesh_path}
    [-o {output_path}]
    [-r {resolution}] [-q {render_quality}]
    [-p {render_pass1}] [-p {render_pass2}] [-p {render_pass3}] ...
    [-f {img_format}] [-h {hdr_map_path}] [-e {render_engine}] [--no-background]
"""

from pathlib import Path
from textwrap import dedent
from typing import List, Optional, Tuple

from click import Choice
from rich.pretty import pretty_repr
from typer import Argument, Option, Typer
from typing_extensions import Annotated

import xrfeitoria as xf
from xrfeitoria.data_structure.constants import ImageFileFormatEnum, RenderEngineEnumBlender, RenderOutputEnumBlender
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.utils.tools import Logger

RENDER_SAMPLES = {'low': 64, 'medium': 256, 'high': 1024}
app = Typer(pretty_exceptions_show_locals=False)


@app.command()
def main(
    # path config
    mesh_path: Annotated[
        Path,
        Argument(
            ...,
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            help='filepath of the mesh to be renderer',
        ),
    ],
    output_path: Annotated[
        Path,
        Option('--output-path', '-o', resolve_path=True, help='output path of the rendered images'),
    ] = Path('output').resolve(),
    # render config
    resolution: Annotated[
        Tuple[int, int],
        Option('--resolution', '-r', help='resolution of the rendered images'),
    ] = (512, 512),
    render_quality: Annotated[
        str,
        Option(
            '--render-quality',
            '-q',
            case_sensitive=False,
            click_type=Choice(RENDER_SAMPLES.keys()),
            help=(
                'ignored in eevee. '
                f'quality (for cycles) of the rendered images which controlled by render samples: {RENDER_SAMPLES}'
            ),
        ),
    ] = 'low',
    render_passes: Annotated[
        List[str],
        Option(
            '--render-pass',
            '-p',
            case_sensitive=False,
            click_type=Choice([e.name for e in RenderOutputEnumBlender]),
            help='render passes to be rendered',
        ),
    ] = ['img'],
    img_format: Annotated[
        str,
        Option(
            '--img-format',
            '-f',
            case_sensitive=False,
            click_type=Choice([e.name for e in ImageFileFormatEnum]),
            help='image format of the rendered images',
        ),
    ] = 'png',
    transparent: Annotated[
        bool,
        Option('--transparent/--no-transparent', help='render result with transparent background'),
    ] = True,
    # light config
    hdr_map_path: Annotated[
        Optional[Path],
        Option('--hdr-map-path', '-h', exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    ] = None,
    # engine config
    blender_exec: Annotated[
        Path,
        Option('--blender-exec', help='path to blender executable, e.g. /usr/bin/blender'),
    ] = None,
    render_engine: Annotated[
        str,
        Option(
            '--render-engine',
            '-e',
            case_sensitive=False,
            click_type=Choice([e.name for e in RenderEngineEnumBlender]),
            help='render engine to be used',
        ),
    ] = 'cycles',
    background: Annotated[
        bool,
        Option('--background/--no-background', '-b', help='run blender in background mode'),
    ] = True,
    # misc
    debug: Annotated[
        bool,
        Option('--debug/--no-debug', help='log in debug mode'),
    ] = False,
):
    """Render a mesh with blender to output_path."""
    logger = Logger.setup_logging(level='DEBUG' if debug else 'INFO')
    if render_engine == 'eevee':
        render_quality = 'low'

    logger.info(
        dedent(
            f"""\
            :rocket: Starting:
            Executing render with the following parameters:
            ---------------------------------------------------------
            [yellow]# path config[/yellow]
            - mesh_path: {mesh_path}
            - output_path: {output_path}
            [yellow]# render config[/yellow]
            - resolution: {resolution}
            - render_quality: {render_quality} ({RENDER_SAMPLES[render_quality]} render samples)
            - render_passes: {render_passes}
            - img_format: {img_format}
            - transparent: {transparent}
            - hdr_map_path: {hdr_map_path}
            [yellow]# engine config[/yellow]
            - blender_exec: {blender_exec}
            - render_engine: {render_engine}
            - background: {background}
            [yellow]# misc[/yellow]
            - debug: {debug}
            ---------------------------------------------------------"""
        )
    )

    # warning
    if background and RenderEngineEnumBlender.get(render_engine) != RenderEngineEnumBlender.cycles:
        logger.warning(':exclamation_mark: Blender in [u]background[/u] using [u]eevee[/u] may cause unexpected error.')

    seq_name = mesh_path.stem
    camera_name = 'camera'

    with xf.init_blender(exec_path=blender_exec, background=background) as xf_runner:
        with xf_runner.Sequence.new(seq_name=seq_name) as seq:
            actor = seq.import_actor(actor_name='actor', file_path=mesh_path, stencil_value=255)
            actor.set_origin_to_center()
            actor.location = (0, 0, 0)

            radius = max(actor.dimensions)
            actor_bbox = actor.bound_box
            actor_bbox_center = (
                (actor_bbox[0][0] + actor_bbox[1][0]) / 2,
                (actor_bbox[0][1] + actor_bbox[1][1]) / 2,
                (actor_bbox[0][2] + actor_bbox[1][2]) / 2,
            )
            camera_location = (
                actor_bbox_center[0],
                actor_bbox_center[1] - radius,
                actor_bbox_center[2],
            )
            camera_rotation = xf_runner.utils.get_rotation_to_look_at(
                location=camera_location,
                target=actor_bbox_center,
            )
            seq.spawn_camera(
                camera_name=camera_name,
                location=camera_location,
                rotation=camera_rotation,
            )
            # set light
            if hdr_map_path:
                xf_runner.utils.set_hdr_map(hdr_map_path=hdr_map_path)

            # frame range
            frame_start, frame_end = xf_runner.utils.get_keys_range()
            xf_runner.utils.set_frame_range(start=frame_start, end=frame_end)

            # add to renderer
            seq.add_to_renderer(
                output_path=output_path,
                resolution=resolution,
                render_passes=[RenderPass(render_pass, img_format) for render_pass in render_passes],
                render_engine=render_engine,
                render_samples=RENDER_SAMPLES[render_quality],
                transparent_background=transparent,
                arrange_file_structure=True,
            )

        xf_runner.render()

    img_paths = {
        render_pass: (output_path / seq_name / render_pass / camera_name / f'0000.{img_format}').as_posix()
        for render_pass in render_passes
    }
    logger.info(
        f':chequered_flag: [bold green]Finished![/bold green] Check the rendered images in:\n{pretty_repr(img_paths)}'
    )


if __name__ == '__main__':
    app()
