from pathlib import Path
from typing import Union

import numpy as np

from .motion import Motion, SMPLMotion, SMPLXMotion


def load_amass_motion(input_amass_smplx_path: Union[Path, str]) -> Motion:
    """Load AMASS SMPLX motion data.

    Args:
        input_amass_smplx_path (Union[Path, str]): Path to AMASS SMPLX motion data.

    Returns:
        Motion: Motion data, which consists of data read from AMASS file.
    """
    input_amass_smplx_path = Path(input_amass_smplx_path).resolve()
    if not input_amass_smplx_path.exists():
        raise ValueError(f'Not exist: {input_amass_smplx_path}')
    # Use AMASS motion
    # src_actor_name = "SMPLX"
    amass_smplx_data = np.load(input_amass_smplx_path, allow_pickle=True)
    src_motion = SMPLXMotion.from_amass_data(amass_smplx_data, insert_rest_pose=True)

    return src_motion


def load_humandata_motion(input_humandata_path: Union[Path, str]) -> Motion:
    """Load humandata SMPL / SMPLX motion data.
    HumanData is a structure of smpl/smplx data defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md

    Args:
        input_humandata_path (Union[Path, str]): Path to humandata SMPL / SMPLX motion data.

    Returns:
        Motion: Motion data, which consists of data read from humandata file.
    """
    input_humandata_path = Path(input_humandata_path).resolve()
    if not input_humandata_path.exists():
        raise ValueError(f'Not exist: {input_humandata_path}')
    # Use humandata SMPL / SMPLX
    humandata = np.load(input_humandata_path, allow_pickle=True)
    if 'smpl' in humandata:
        # src_actor_name = "SMPL"
        smpl_data = humandata['smpl'].item()
        src_motion = SMPLMotion.from_smpl_data(smpl_data=smpl_data, insert_rest_pose=False)
    else:
        # src_actor_name = "SMPLX"
        smplx_data = humandata['smplx'].item()
        src_motion = SMPLXMotion.from_smplx_data(smplx_data=smplx_data, insert_rest_pose=False)

    return src_motion


if __name__ == '__main__':
    motion = load_amass_motion('amass-smplx_n/ACCAD/s001/EricCamper04_stageii.npz')
    motion_data = motion.get_motion_data()
