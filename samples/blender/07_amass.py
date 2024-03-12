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
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.rpc import remote_blender
from xrfeitoria.utils import setup_logger
from xrfeitoria.utils.anim import dump_humandata, load_amass_motion

# prepare the assets
####################
root = Path('.cache/sample-amass').resolve()  # modify this to your own path

# 1. Download Amass from https://amass.is.tue.mpg.de/download.php
# For example, download ACCAD (SMPL-X N) from https://download.is.tue.mpg.de/download.php?domain=amass&sfile=amass_per_dataset/smplx/neutral/mosh_results/ACCAD.tar.bz2
# and use `ACCAD/s001/EricCamper04_stageii.npz` from the uncompressed folder
amass_file = root / 'EricCamper04_stageii.npz'

# 2.1 Download SMPL-XL model from https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/SMPL-XL-001.fbx
# or from https://openxlab.org.cn/datasets/OpenXDLab/SynBody/tree/main/Assets
# With downloading this, you are agreeing to CC BY-NC-SA 4.0 License (https://creativecommons.org/licenses/by-nc-sa/4.0/).
smpl_xl_file = root / 'SMPL-XL-001.fbx'
# 2.2 Download the meta information from https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/assets/SMPL-XL-001.npz
smpl_xl_meta_file = root / 'SMPL-XL-001.npz'

# 3. Define the output file path
seq_name = 'seq_amass'
output_path = Path(__file__).resolve().parents[2] / 'output/samples/blender' / Path(__file__).stem
output_path.mkdir(parents=True, exist_ok=True)
saved_humandata_file = output_path / seq_name / 'output.npz'
saved_blend_file = output_path / seq_name / 'output.blend'


@remote_blender()
def apply_scale(actor_name: str):
    import bpy

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[actor_name].select_set(True)
    bpy.ops.object.transform_apply(scale=True)


def main(background: bool = False):
    logger = setup_logger()

    motion = load_amass_motion(amass_file)
    motion.convert_fps(30)  # convert the motion from 120fps (amass) to 30fps
    motion_data = motion.get_motion_data()

    # modify this to your blender executable path
    xf_runner = xf.init_blender(
        exec_path='C:/Program Files/Blender Foundation/Blender 3.6/blender.exe', background=background
    )

    with xf_runner.Sequence.new(seq_name=seq_name, seq_length=motion.n_frames) as seq:
        # Import SMPL-XL model
        actor = xf_runner.Actor.import_from_file(smpl_xl_file)
        apply_scale(actor.name)  # SMPL-XL model is imported with scale, we need to apply scale to it

        # Apply motion data to the actor
        logger.info('Applying motion data')
        xf_runner.utils.apply_motion_data_to_actor(motion_data=motion_data, actor_name=actor.name)
        # Save the motion data as annotation in humandata format defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md
        dump_humandata(motion, save_filepath=saved_humandata_file, meta_filepath=smpl_xl_meta_file)

        # Modify the frame range to the length of the motion
        frame_start, frame_end = xf_runner.utils.get_keys_range()
        xf_runner.utils.set_frame_range(frame_start, frame_end)
        # env
        xf_runner.utils.set_env_color(color=(1, 1, 1, 1))

        #
        camera = xf_runner.Camera.spawn(location=(0, -2.5, 0.6), rotation=(90, 0, 0))

        seq.add_to_renderer(
            output_path=output_path,
            resolution=(1920, 1080),
            render_passes=[RenderPass('img', 'png')],
            render_engine='eevee',
        )

    # Save the blend file
    xf_runner.utils.save_blend(saved_blend_file, pack=True)

    # render
    xf_runner.render()

    logger.info('🎉 [bold green]Success!')
    output_img = output_path / seq_name / 'img' / camera.name / '0000.png'
    if output_img.exists():
        logger.info(f'Check the output in "{output_img.as_posix()}"')
    if not background:
        input('You can check the result in the blender window. Press Any Key to Exit...')

    # Close the blender process
    xf_runner.close()

    logger.info(f'You can use Blender to check the result in "{saved_blend_file.as_posix()}"')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--background', '-b', action='store_true')
    args = parser.parse_args()

    main(background=args.background)
