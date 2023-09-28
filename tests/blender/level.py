"""
>>> python -m tests.blender.level
"""
from pathlib import Path

from loguru import logger

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.factory import XRFeitoriaBlender

from ..config import assets_path
from ..utils import __timer__, _init_blender, setup_logger

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/tests/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')

hdr_map_path = assets_path['hdr_sample']
bunny_obj_path = assets_path['bunny']
actor_path = assets_path['SMPL_XL']
motion_path = assets_path['motion_1']
blend_sample = assets_path['blend_sample']


def seq_simple(xf_runner: XRFeitoriaBlender, seq_name: str = 'seq_simple'):
    with xf_runner.Sequence.new(seq_name=seq_name, level='Scene', seq_length=1) as seq:
        camera = xf_runner.Camera('Camera')
        seq.use_camera(camera)

        seq.add_to_renderer(
            output_path=output_path / f'{seq.name}',
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'exr'),
            ],
            resolution=[512, 512],
            render_engine='CYCLES',
            render_samples=16,
            transparent_background=False,
            arrange_file_structure=True,
        )


def level_test(debug=False, background=False):
    setup_logger(debug=debug)
    with _init_blender(background=background, new_process=True, cleanup=False, project_path=blend_sample) as xf_runner:
        with __timer__('create and sequence'):
            seq_simple(xf_runner)

        # save blend
        # blend_file = output_path / 'source.blend'
        # xf_runner.utils.save_blend(save_path=blend_file)

        with __timer__('render'):
            xf_runner.render()

    logger.info('🎉 [bold green]level render tests passed!')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    level_test(debug=args.debug, background=args.background)
