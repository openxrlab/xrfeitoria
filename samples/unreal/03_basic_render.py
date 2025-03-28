"""
>>> python -m samples.unreal.03_basic_render

This is a script to render a preset level in unreal.
"""

from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.utils import setup_logger

from ..config import unreal_exec, unreal_project

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/samples/unreal/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'unreal.log'

seq_name = 'seq_preset'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)
    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # There are many assets already made by others, including levels, sequences, cameras, meshes, etc.
    # Using xrfeitoria enables convenient utilization of these assets.

    # open a pre-made sequence, which has a corresponding level
    # the sequence data is under /Game/XRFeitoriaUnreal/Sequences/{seq_name}_data
    with xf_runner.sequence(seq_name=seq_name) as seq:
        # use the camera in the level to render
        camera = xf_runner.Camera('Camera')
        camera_name = camera.name

        # clear the render jobs in the renderer
        xf_runner.Renderer.clear()
        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path,
            render_passes=[RenderPass('img', 'png')],
            resolution=[1280, 720],
        )

    # render all jobs
    xf_runner.render()

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # close the unreal process
    xf_runner.close()

    output_img = output_path / seq_name / 'img' / camera_name / '0000.png'
    if output_img.exists():
        logger.info(f'Check the output in "{output_img.as_posix()}"')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
