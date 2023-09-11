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
    render_pass: Annotated[
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
    ] = 'eevee',
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
            - render_pass: {render_pass}
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

    with xf.init_blender(exec_path=blender_exec, background=background) as xf_runner:
        with xf_runner.Sequence.new(seq_name='seq') as seq:
            actor = seq.import_actor(actor_name='actor', file_path=mesh_path, stencil_value=255)
            actor.set_origin_to_center()
            actor.location = (0, 0, 0)
            actor.rotation = (0, 0, 0)

            radius = max(actor.dimensions)
            # TODO: more reasonable camera options
            camera = seq.spawn_camera(camera_name='camera', location=(0, 0, radius), rotation=(0, 0, 0))
            camera_name = camera.name
            # set light
            if hdr_map_path:
                xf_runner.utils.set_hdr_map(hdr_map_path=hdr_map_path)
            else:
                xf_runner.utils.set_env_color(color=(1, 1, 1, 1))

            # frame range
            frame_start, frame_end = xf_runner.utils.get_keys_range()
            xf_runner.utils.set_frame_range(start=frame_start, end=frame_end)

            # add to renderer
            render_passes = [RenderPass(rp, img_format) for rp in render_pass]
            seq.add_to_renderer(
                output_path=output_path,
                resolution=resolution,
                render_passes=render_passes,
                render_engine=render_engine,
                render_samples=RENDER_SAMPLES[render_quality],
                transparent_background=transparent,
                arrange_file_structure=True,
            )

        xf_runner.render()

    img_path = output_path / render_pass[0] / camera_name / f'0000.{img_format}'
    if not img_path.exists():
        img_path = output_path
    logger.info(
        f':chequered_flag: [bold green]Finished![/bold green] Check the rendered images in "{img_path.as_posix()}"'
    )


if __name__ == '__main__':
    app()
