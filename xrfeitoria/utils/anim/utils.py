"""Utilities for animation data loading and dumping."""

from pathlib import Path
from typing import Optional, Union

import numpy as np
from scipy.spatial.transform import Rotation as spRotation

from ...actor.actor_base import ActorBase
from ...data_structure.constants import PathLike
from .motion import SMPLMotion, SMPLXMotion


def load_amass_motion(input_amass_smpl_x_path: PathLike, is_smplx: bool = True) -> Union[SMPLMotion, SMPLXMotion]:
    """Load AMASS SMPLX motion data. Only for SMPLX motion for now.

    Args:
        input_amass_smpl_x_path (PathLike): Path to AMASS SMPL/SMPLX motion data.

    Returns:
        Union[SMPLMotion, SMPLXMotion]: Motion data, which consists of data read from AMASS file.
    """
    input_amass_smpl_x_path = Path(input_amass_smpl_x_path).resolve()
    if not input_amass_smpl_x_path.exists():
        raise ValueError(f'Not exist: {input_amass_smpl_x_path}')
    # Use AMASS motion
    # src_actor_name = "SMPLX"
    amass_smpl_x_data = np.load(input_amass_smpl_x_path, allow_pickle=True)
    if is_smplx:
        src_motion = SMPLXMotion.from_amass_data(amass_smpl_x_data, insert_rest_pose=True)
    else:
        src_motion = SMPLMotion.from_amass_data(amass_smpl_x_data, insert_rest_pose=True)
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


def dump_humandata(
    motion: Union[SMPLMotion, SMPLXMotion],
    save_filepath: PathLike,
    meta_filepath: PathLike,
    actor_name: Optional[str] = None,
) -> None:
    """Dump human data to a file. This function must be associate with a meta file
    provided by SMPL-XL.

    Args:
        motion (Union[SMPLMotion, SMPLXMotion]): The motion data to be dumped.
        save_filepath (PathLike): The file path to save the dumped data.
        meta_filepath (PathLike): The file path to the meta information, storing the parameters of the SMPL-XL model.
        actor_name (Optional[str], optional): The name of the actor. Defaults to None.

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
                'meta': {'gender': 'neutral', 'actor_name': '(XF)actor-001'},  # optional
            }
    """
    meta_info = np.load(meta_filepath, allow_pickle=True)
    if 'smplx' in meta_info.keys():
        smpl_x = meta_info['smplx'].item()
    elif 'smpl' in meta_info.keys():
        smpl_x = meta_info['smpl'].item()

    _meta_ = meta_info['meta'].item()
    if actor_name:
        _meta_['actor_name'] = actor_name

    motion.dump_humandata(
        filepath=save_filepath,
        betas=smpl_x['betas'],
        meta=_meta_,
        global_orient_offset=smpl_x['global_orient'],
        transl_offset=smpl_x['transl'],
        root_location_t0=smpl_x['root_location_t0'],
        pelvis_location_t0=smpl_x['pelvis_location_t0'],
    )


def refine_smpl_x(
    smpl_x_file: Path,
    replace_smpl_x_file: bool = False,
    offset_location: np.ndarray = np.zeros(3),
    offset_rotation: np.ndarray = np.eye(3),
) -> None:
    """Refine translation and rotation of SMPL-X parameters."""

    # Load SMPL-X data
    smpl_x_file = Path(smpl_x_file)
    data = dict(np.load(smpl_x_file, allow_pickle=True))
    if 'smplx' in data.keys():
        smpl_x_type = 'smplx'
    elif 'smpl' in data.keys():
        smpl_x_type = 'smpl'
    else:
        raise ValueError(f'Unknown keys in {smpl_x_file}: {data.keys()}')

    # Convert offset_rotation
    if offset_rotation.shape == (3, 3):
        offset_rotation = spRotation.from_matrix(offset_rotation)
    elif offset_rotation.shape == (4,):
        offset_rotation = spRotation.from_quat(offset_rotation)
    else:
        raise ValueError('Please convert offset_rotation to 3x3 matrix or 4-dim quaternion.')

    smpl_x_data = data[smpl_x_type].item()
    global_orient = smpl_x_data['global_orient']
    global_orient = spRotation.from_rotvec(global_orient)
    global_orient = (offset_rotation * global_orient).as_rotvec()
    transl = smpl_x_data['transl']
    transl = offset_rotation.apply(transl - transl[0]) + transl[0]
    transl += offset_location

    smpl_x_data['global_orient'] = global_orient.astype(np.float32)
    smpl_x_data['transl'] = transl.astype(np.float32)
    data[smpl_x_type] = smpl_x_data

    if replace_smpl_x_file:
        np.savez(smpl_x_file, **data)
    else:
        np.savez(smpl_x_file.parent / f'{smpl_x_file.stem}_refined.npz', **data)


def refine_smpl_x_from_actor_info(smpl_x_file: Path, actor_info_file: Path, replace_smpl_x_file: bool = False):
    """Refine translation and rotation of SMPL-X parameters from actor info file."""
    actor_info = np.load(actor_info_file, allow_pickle=True)
    location = actor_info['location']
    rotation = actor_info['rotation']
    assert np.all(location == location[0]) and np.all(rotation == rotation[0])

    refine_smpl_x(
        smpl_x_file=smpl_x_file,
        replace_smpl_x_file=replace_smpl_x_file,
        offset_location=location[0],
        offset_rotation=rotation[0],
    )


if __name__ == '__main__':
    """Python -m xrfeitoria.utils.anim.utils."""
    motion = load_amass_motion('.cache/ACCAD/s001/EricCamper04_stageii.npz')
    motion_data = motion.get_motion_data()
    dump_humandata(motion, '.cache/SMPL-XL_test.npz', '.cache/SMPL-XL-001.npz')
    print('Done')
