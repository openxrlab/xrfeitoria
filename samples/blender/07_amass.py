"""
>>> python -m samples.blender.07_amass

This is a script to demonstrate importing Amass motion and applying it to SMPL-XL model.
Before running this script, please download SMPL-XL model and Amass dataset first,
you can find the download links in the comments in main function.

** It is recommended to run this script with Blender >= 3.6 **
"""
import xrfeitoria as xf
from xrfeitoria.rpc import remote_blender
from xrfeitoria.utils.tools import Logger

from ..anim.utils import load_amass_motion


@remote_blender()
def apply_scale(actor_name: str):
    import bpy

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[actor_name].select_set(True)
    bpy.ops.object.transform_apply(scale=True)


def main():
    logger = Logger.setup_logging()

    # Download Amass from https://amass.is.tue.mpg.de/download.php
    # For example, download ACCAD (SMPL-X N), and use any motion file from uncompressed folder
    motion = load_amass_motion('ACCAD/s001/EricCamper04_stageii.npz')  # modify this to motion file in absolute path
    motion_data = motion.get_motion_data()

    xf_runner = xf.init_blender(
        exec_path='C:/Program Files/Blender Foundation/Blender 3.3/blender.exe'
    )  # modify this to your blender executable path
    # Download SMPL-XL model from https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/SMPL-XL-001.fbx
    # or from https://openxlab.org.cn/datasets/OpenXDLab/SynBody/tree/main/Assets
    # With downloading this, you are agreeing to CC BY-NC-SA 4.0 License (https://creativecommons.org/licenses/by-nc-sa/4.0/)

    # import SMPL-XL model
    actor = xf_runner.Actor.import_from_file('SMPL-XL-001.fbx')  # modify this to SMPL-XL model file in absolute path
    apply_scale(actor.name)  # SMPL-XL model is imported with scale, we need to apply scale to it
    xf_runner.utils.apply_motion_data_to_actor(motion_data=motion_data, actor_name=actor.name)

    # modify the frame range to the length of the motion
    frame_start, frame_end = xf_runner.utils.get_keys_range()
    xf_runner.utils.set_frame_range(frame_start, frame_end)

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # close the blender process
    xf_runner.close()


if __name__ == "__main__":
    main()
