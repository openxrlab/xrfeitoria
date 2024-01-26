"""Utilities for animation data loading and dumping."""
from pathlib import Path
from typing import Union

import numpy as np

from ...data_structure.constants import PathLike
from .motion import Motion, SMPLMotion, SMPLXMotion


def load_amass_motion(input_amass_smplx_path: PathLike) -> SMPLXMotion:
    """Load AMASS SMPLX motion data. Only for SMPLX motion for now.

    Args:
        input_amass_smplx_path (PathLike): Path to AMASS SMPLX motion data.

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


def load_humandata_motion(input_humandata_path: PathLike) -> Union[SMPLMotion, SMPLXMotion]:
    """Load humandata SMPL / SMPLX motion data.

    HumanData is a structure of smpl/smplx data defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md

    Args:
        input_humandata_path (PathLike): Path to humandata SMPL / SMPLX motion data.

    Returns:
        Union[SMPLMotion, SMPLXMotion]: Motion data, which consists of data read from humandata file.
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


def dump_humandata(motion: SMPLXMotion, save_filepath: PathLike, meta_filepath: PathLike) -> None:
    """Dump human data to a file. This function must be associate with a meta file
    provided by SMPL-XL.

    Args:
        motion (SMPLXMotion): Motion data to dump.
        save_filepath (PathLike): The file path to save the dumped data.
        meta_filepath (PathLike): The file path to the meta information, storing the parameters of the SMPL-XL model.

    Note:
        HumanData is a structure of smpl/smplx data defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md

        The humandata file is a npz file containing the following keys:

        .. code-block:: python

            humandata = {
                '__data_len__': n_frames,
                'smplx': {
                    'betas': betas,  # (1, 10)
                    'transl': transl,  # (n_frames, 3)
                    'global_orient': global_orient,  # (n_frames, 3)
                    'body_pose': body_pose,  # (n_frames, 63)
                    'jaw_pose': jaw_pose,  # (n_frames, 3)
                    'leye_pose': leye_pose,  # (n_frames, 3)
                    'reye_pose': reye_pose,  # (n_frames, 3)
                    'left_hand_pose': left_hand_pose,  # (n_frames, 45)
                    'right_hand_pose': right_hand_pose,  # (n_frames, 45)
                    'expression': expression,  # (n_frames, 10)
                },
                'meta': {'gender': 'neutral'},  # optional
            }
    """
    meta_info = np.load(meta_filepath, allow_pickle=True)
    smplx = meta_info['smplx'].item()
    motion.dump_humandata(
        filepath=save_filepath,
        betas=smplx['betas'],
        meta=meta_info['meta'].item(),
        global_orient_offset=smplx['global_orient'],
        transl_offset=smplx['transl'],
        root_location_t0=smplx['root_location_t0'],
        pelvis_location_t0=smplx['pelvis_location_t0'],
    )


if __name__ == '__main__':
    """Python -m xrfeitoria.utils.anim.utils."""
    motion = load_amass_motion('.cache/ACCAD/s001/EricCamper04_stageii.npz')
    motion_data = motion.get_motion_data()
    dump_humandata(motion, '.cache/SMPL-XL_test.npz', '.cache/SMPL-XL-001.npz')
    print('Done')
