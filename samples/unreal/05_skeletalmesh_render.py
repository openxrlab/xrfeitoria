"""
>>> python -m samples.unreal.05_skeletalmesh_render

This is a script to render skeletal meshes in unreal.
"""

from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.utils import setup_logger

from ..config import assets_path, unreal_exec, unreal_project

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/samples/unreal/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'unreal.log'

level_path = '/Game/Levels/Playground'  # pre-defined level
seq_name = 'seq_skeletalmesh'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)
    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # import actor from file and its animation
    SMPL_XL_path = xf_runner.utils.import_asset(path=assets_path['SMPL_XL'])
    animation_path = xf_runner.utils.import_anim(
        path=assets_path['motion_1'], skeleton_path=f'{SMPL_XL_path}_Skeleton'
    )[0]

    with xf_runner.sequence(seq_name=seq_name, level=level_path, seq_length=200, replace=True) as seq:
        seq.show()

        # add a camera in sequence to render
        camera = seq.spawn_camera(location=(0, -2, 1), rotation=(0, 0, 90), fov=90)
        camera_name = camera.name

        actor = seq.spawn_actor(
            SMPL_XL_path,
            anim_asset_path=animation_path,
            location=(0, 0, 0),
            rotation=(0, 0, 180),
            scale=(100, 100, 100),
            stencil_value=1,
        )

        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path,
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'exr'),  # in png format, annotations would apply gamma correction (2.2)
            ],
            resolution=[1280, 720],
        )

    # render all jobs
    xf_runner.render()

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    xf_runner.close()

    output_img = output_path / seq_name / 'img' / camera_name / '0000.png'
    if output_img.exists():
        logger.info(f'Check the output in "{output_img.as_posix()}"')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
