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
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.utils import setup_logger
from xrfeitoria.utils.anim import dump_humandata, load_amass_motion, refine_smpl_x_from_actor_info

from ..config import unreal_exec, unreal_project

# prepare the assets
####################
assets_root = Path('.cache/sample-amass').resolve()  # modify this to your own path

# 1. Download Amass from https://amass.is.tue.mpg.de/download.php
# For example, download ACCAD (SMPL-X N) from https://download.is.tue.mpg.de/download.php?domain=amass&sfile=amass_per_dataset/smplx/neutral/mosh_results/ACCAD.tar.bz2
# and use `ACCAD/s001/EricCamper04_stageii.npz` from the uncompressed folder
amass_file = assets_root / 'EricCamper04_stageii.npz'

# 2.1 Download SMPL-XL model from https://github.com/openxrlab/xrfeitoria/releases/download/v0.1.0/assets--SMPL-XL-001.fbx
# or from https://openxlab.org.cn/datasets/OpenXDLab/SynBody/tree/main/Assets
# With downloading this, you are agreeing to CC BY-NC-SA 4.0 License (https://creativecommons.org/licenses/by-nc-sa/4.0/).
smpl_xl_file = assets_root / 'SMPL-XL-001.fbx'
# 2.2 Download the meta information from https://github.com/openxrlab/xrfeitoria/releases/download/v0.1.0/assets--SMPL-XL-001.npz
smpl_xl_meta_file = assets_root / 'SMPL-XL-001.npz'

# 3. Define the output file path
seq_name = Path(__file__).stem
output_path = Path(__file__).resolve().parents[2] / 'output/samples/unreal'
seq_dir = output_path / seq_name
saved_humandata_file = seq_dir / 'smplx' / 'output.npz'


def main(background: bool = False):
    logger = setup_logger()

    motion = load_amass_motion(amass_file)
    motion.convert_fps(30)  # convert the motion from 120fps (amass) to 30fps
    motion.cut_motion(end_frame=10)  # cut the motion to 10 frames, for demonstration purpose
    motion_data = motion.get_motion_data()

    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # Import SMPL-XL model
    actor_path = xf_runner.utils.import_asset(smpl_xl_file, replace=False)

    with xf_runner.sequence(
        seq_name=seq_name, level='/Game/Levels/Playground', seq_length=motion.n_frames, replace=True
    ) as seq:
        seq.show()

        # Spawn the actor, and add motion data as FK animation
        actor = seq.spawn_actor(
            actor_asset_path=actor_path,
            location=(3, 0, 0),
            rotation=(0, 0, 0),
            stencil_value=1,
            motion_data=motion_data,
        )
        actor_name = actor.name

        camera = seq.spawn_camera(
            location=(3, 2.5, 0.6),
            rotation=(0, 0, -90),
        )

        # Add render job to renderer
        seq.add_to_renderer(
            output_path=output_path,
            resolution=(1920, 1080),
            render_passes=[RenderPass('img', 'jpg')],
            export_skeleton=True,
            export_vertices=True,
        )

    # Save the motion data as annotation in humandata format defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md
    dump_humandata(motion, save_filepath=saved_humandata_file, meta_filepath=smpl_xl_meta_file, actor_name=actor_name)

    # render
    xf_runner.render()

    # refine smplx parameters
    refine_smpl_x_from_actor_info(
        smpl_x_filepath=saved_humandata_file,
        meta_filepath=smpl_xl_meta_file,
        actor_info_file=seq_dir / 'actor_infos' / f'{actor_name}.npz',
        replace_smpl_x_file=True,
    )

    logger.info('🎉 [bold green]Success!')
    output_img = seq_dir / 'img' / camera.name / '0000.png'
    if output_img.exists():
        logger.info(f'Check the output in "{output_img.as_posix()}"')
    if not background:
        input('You can check the result in the unreal window. Press Any Key to Exit...')

    # Close the unreal process
    xf_runner.close()

    logger.info(f'You can use Unreal to check the result in "{Path(unreal_project).as_posix()}"')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--background', '-b', action='store_true')
    args = parser.parse_args()

    main(background=args.background)
