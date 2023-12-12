"""
>>> python -m samples.unreal.07_amass

This is a script to demonstrate importing Amass motion and applying it to SMPL-XL model.
Before running this script, please download `SMPL-XL model` and `Amass dataset` first,
you can find the download links in the comments in main function.

SMPL-XL: a parametric human model based on SMPL-X in a layered representation, introduced in https://synbody.github.io/
Amass: a large database of human motion, introduced in https://amass.is.tue.mpg.de/
"""
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.utils import setup_logger
from xrfeitoria.utils.anim.utils import dump_humandata, load_amass_motion

from ..config import unreal_exec, unreal_project

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
saved_humandata_file = root / 'output.npz'


def main(background: bool = False):
    logger = setup_logger()

    motion = load_amass_motion(amass_file)
    motion.convert_fps(30)  # convert the motion from 120fps (amass) to 30fps
    motion_data = motion.get_motion_data()

    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # Import SMPL-XL model
    actor_path = xf_runner.utils.import_asset(smpl_xl_file)

    with xf_runner.Sequence.new(
        seq_name='seq_amass', level='/Game/Levels/Playground', seq_length=200, replace=True
    ) as seq:
        seq.show()

        # Spawn the actor, and add motion data as FK animation
        actor = seq.spawn_actor(
            actor_asset_path=actor_path,
            location=(0, 0, 0),
            rotation=(0, 0, 0),
            stencil_value=1,
            motion_data=motion_data,
        )

    # Save the motion data as annotation in humandata format defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md
    dump_humandata(motion, save_filepath=saved_humandata_file, meta_filepath=smpl_xl_meta_file)

    logger.info('🎉 [bold green]Success!')
    if not background:
        input('You can check the result in the unreal window. Press Any Key to Exit...')

    # Close the unreal process
    xf_runner.close()

    logger.info(f'You can use Unreal to check the result in "{unreal_project.as_posix()}"')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--background', '-b', action='store_true')
    args = parser.parse_args()

    main(background=args.background)
