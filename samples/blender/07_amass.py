"""
>>> python -m samples.blender.07_amass

This is a script to demonstrate importing Amass motion and applying it to SMPL-XL model.
Before running this script, please download `SMPL-XL model` and `Amass dataset` first,
you can find the download links in the comments in main function.

SMPL-XL: a parametric human model based on SMPL-X in a layered representation, introduced in https://synbody.github.io/
Amass: a large database of human motion, introduced in https://amass.is.tue.mpg.de/

** It is recommended to run this script with Blender >= 3.6 **
"""
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.rpc import remote_blender
from xrfeitoria.utils import setup_logger
from xrfeitoria.utils.anim.utils import dump_humandata, load_amass_motion

root = Path('.cache/sample-amass')
amass_file = root / 'EricCamper04_stageii.npz'
smpl_xl_file = root / 'SMPL-XL-001.fbx'
smpl_xl_meta_file = root / 'SMPL-XL-001.npz'
saved_blend_file = root / 'output.blend'
saved_humandata_file = root / 'output.npz'


@remote_blender()
def apply_scale(actor_name: str):
    import bpy

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[actor_name].select_set(True)
    bpy.ops.object.transform_apply(scale=True)


def main(background: bool = False):
    logger = setup_logger()

    # Download Amass from https://amass.is.tue.mpg.de/download.php
    # For example, download ACCAD (SMPL-X N), and use any motion file from the uncompressed folder
    motion = load_amass_motion(amass_file)  # modify this to motion file in absolute path
    motion.convert_fps(30)  # convert the motion from 120fps (amass) to 30fps
    motion_data = motion.get_motion_data()

    xf_runner = xf.init_blender(
        exec_path='C:/Program Files/Blender Foundation/Blender 3.6/blender.exe',
        background=background,
    )  # modify this to your blender executable path

    # SMPL-XL model
    # 1. Download SMPL-XL model from https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/SMPL-XL-001.fbx
    # or from https://openxlab.org.cn/datasets/OpenXDLab/SynBody/tree/main/Assets
    # With downloading this, you are agreeing to CC BY-NC-SA 4.0 License (https://creativecommons.org/licenses/by-nc-sa/4.0/)
    # 2. Import SMPL-XL model
    actor = xf_runner.Actor.import_from_file(smpl_xl_file)  # modify this to SMPL-XL model file in absolute path
    apply_scale(actor.name)  # SMPL-XL model is imported with scale, we need to apply scale to it

    logger.info('Applying motion data')
    xf_runner.utils.apply_motion_data_to_actor(motion_data=motion_data, actor_name=actor.name)
    dump_humandata(motion, save_filepath=saved_humandata_file, meta_filepath=smpl_xl_meta_file)

    # Modify the frame range to the length of the motion
    frame_start, frame_end = xf_runner.utils.get_keys_range()
    xf_runner.utils.set_frame_range(frame_start, frame_end)

    # Save the blend file
    xf_runner.utils.save_blend(saved_blend_file, pack=True)

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # Close the blender process
    xf_runner.close()


if __name__ == '__main__':
    from argparse import ArgumentParser

    args = ArgumentParser()
    args.add_argument('--background', '-b', action='store_true')
    args.parse_args()

    main(background=args.background)
