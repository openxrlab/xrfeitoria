from pathlib import Path

import numpy as np

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.rpc import remote_blender
from xrfeitoria.utils import ConverterBlender, setup_logger
from xrfeitoria.utils.anim import dump_humandata, load_amass_motion, refine_smpl_x

amass_file = '.cache/EricCamper04_stageii.npz'
assets_root = Path('E:/SVN/Synbody_ue5_2_for_testing/Assets').resolve()  # modify this to your own path

seq_name = Path(__file__).stem
output_path = Path(__file__).resolve().parents[1] / 'output/blender'
seq_dir = output_path / seq_name
seq_dir.mkdir(parents=True, exist_ok=True)
saved_humandata_file = seq_dir / 'smplx' / 'output.npz'

###############
actor_id = f'{0:07d}'
asset_actor = assets_root / actor_id
asset_blend = asset_actor / 'scene.blend'
smpl_xl_meta_file = asset_actor / 'meta_smplx.npz'

len_frames = 2
###############


@remote_blender()
def apply_location(actor_name: str):
    import bpy

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[actor_name].select_set(True)
    bpy.ops.object.transform_apply(location=True)


def main(background: bool = False, render: bool = False):
    logger = setup_logger()

    motion = load_amass_motion(amass_file, is_smplx=True)
    motion.convert_fps(30)  # convert the motion from 120fps (amass) to 30fps
    # motion.sample_motion(len_frames - 1)
    motion.cut_motion(end_frame=len_frames)
    motion_data = motion.get_motion_data()

    # modify this to your blender executable path
    xf_runner = xf.init_blender(
        exec_path='C:/Program Files/Blender Foundation/Blender 3.6/blender.exe',
        background=background,
        project_path=asset_blend,
        cleanup=False,
    )

    location = (0.5, 0.2, 0.3)
    rotation = (20, 30, 40)

    with xf_runner.sequence(seq_name=seq_name, seq_length=len_frames, level='Scene') as seq:
        #
        actor = xf_runner.Actor(name='Armature')
        apply_location(actor.name)
        actor.location = location
        actor.rotation = rotation

        #
        logger.info('Applying motion data')
        xf_runner.utils.apply_motion_data_to_actor(motion_data=motion_data, actor_name=actor.name)
        dump_humandata(motion, save_filepath=saved_humandata_file, meta_filepath=smpl_xl_meta_file)

        refine_smpl_x(
            smpl_x_filepath=saved_humandata_file,
            meta_filepath=smpl_xl_meta_file,
            offset_location=ConverterBlender.location_from_blender(location),
            offset_rotation=ConverterBlender.rotation_from_blender(rotation),
            replace_smpl_x_file=True,
        )

        logger.info('Exporting vertices')
        xf_runner.utils.export_vertices(export_path=seq_dir / 'vertices')

        if render:
            try:
                camera = xf_runner.Camera.spawn(location=(0, -2.5, 0.6), rotation=(90, 0, 0), camera_name='camera')
            except:
                camera = xf_runner.Camera(name='camera')
            logger.info('Adding render job')
            seq.add_to_renderer(
                output_path=output_path,
                resolution=(1920, 1080),
                render_passes=[RenderPass('img', 'png')],
                render_engine='eevee',
            )
    if render:
        xf_runner.render()

    logger.info(f'output is in "{seq_dir}"')
    xf_runner.close()


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--background', '-b', action='store_true')
    parser.add_argument('--render', '-r', action='store_true')
    args = parser.parse_args()

    main(background=args.background, render=args.render)
