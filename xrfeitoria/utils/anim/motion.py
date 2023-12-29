from collections import OrderedDict
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import numpy as np
from scipy.spatial.transform import Rotation as spRotation
from typing_extensions import Self

from ...data_structure.constants import PathLike
from .constants import (
    NUM_SMPLX_BODYJOINTS,
    SMPL_IDX_TO_JOINTS,
    SMPL_PARENT_IDX,
    SMPLX_HAND_POSES,
    SMPLX_IDX_TO_JOINTS,
    SMPLX_JOINT_NAMES,
    SMPLX_PARENT_IDX,
)
from .transform3d import Matrix

ConverterType = Callable[[np.ndarray], np.ndarray]


class Converter:
    @classmethod
    def vec_humandata2smplx(cls, vector: np.ndarray) -> np.ndarray:
        """From humandata transl (in **OpenCV space**) to SMPLX armature's **pelvis
        local space** in Blender. (The pelvis local space is designed to be the same
        with **SMPL space**.)

        [right, front, up]: (-x, -z, -y) ==> (-x, z, y)

        Args:
            vector (np.ndarray): of shape (N, 3) or (3,)

        Returns:
            np.ndarray: of shape (N, 3) or (3,)
        """
        if vector.shape == (3,):
            vector = np.array([vector[0], -vector[1], -vector[2]], dtype=vector.dtype)
        elif vector.ndim == 2 and vector.shape[1] == 3:
            vector = np.array([vector[:, 0], -vector[:, 1], -vector[:, 2]]).T
        else:
            raise ValueError(f'vector.shape={vector.shape}')
        return vector

    @classmethod
    def vec_smplx2humandata(cls, vector: np.ndarray) -> np.ndarray:
        # vice versa
        return cls.vec_humandata2smplx(vector)

    @classmethod
    def vec_amass2humandata(cls, vector: np.ndarray) -> np.ndarray:
        """From amass transl (pelvis's local space) to humandata transl (in **OpenCV
        space**)

        [right, front, up]: (x, y, z) ==> (-x, -z, -y)

        (CAUTION: we can see amass animation actors face back
            in blender via the smplx add-on)

        Args:
            vector (np.ndarray): of shape (N, 3) or (3,)

        Returns:
            np.ndarray: of shape (N, 3) or (3,)
        """
        if vector.shape == (3,):
            vector = np.array([-vector[0], -vector[2], -vector[1]], dtype=vector.dtype)
        elif vector.ndim == 2 and vector.shape[1] == 3:
            vector = np.array([-vector[:, 0], -vector[:, 2], -vector[:, 1]]).T
        else:
            raise ValueError(f'vector.shape={vector.shape}')
        return vector


class Motion:
    """Wrap motion data. Provide methods to get transform info for 3D calculations.

    The motion data will be used along with `Skeleton` instance in retargeting,
    and the local spaces of bones are all defined in such skeletons.
    """

    BONE_NAMES: List[str]
    BONE_NAME_TO_IDX: Dict[str, int]
    PARENTS: List[int]

    def __init__(
        self,
        transl: np.ndarray,
        body_poses: np.ndarray,
        n_frames: Optional[int] = None,
        fps: float = 30.0,
    ) -> None:
        """Transl & body_poses are in the space of corresponding `Skeleton` instance."""
        transl = transl.reshape([-1, 3])
        body_poses = body_poses.reshape([body_poses.shape[0], -1, 3])
        if n_frames is None:
            n_frames = min(transl.shape[0], body_poses.shape[0])
        self.transl: np.ndarray = transl[:n_frames, :]
        self.body_poses: np.ndarray = body_poses[:n_frames, :, :]
        self.global_orient: np.ndarray = self.body_poses[:, 0, :]

        assert n_frames > 0, f'n_frames={n_frames}'
        self.n_frames = n_frames
        assert fps > 0, f'fps={fps}'
        self.fps = fps

    def _bone2idx(self, bone_name) -> Optional[int]:
        return self.BONE_NAME_TO_IDX.get(bone_name)

    def get_transl(self, frame=0) -> np.ndarray:
        return self.transl[frame, :3]

    def get_global_orient(self, frame=0) -> np.ndarray:
        return self.global_orient[frame, :3]

    def get_bone_rotvec(self, bone_name, frame=0) -> np.ndarray:
        idx = self._bone2idx(bone_name)
        if idx == 0:
            return self.get_global_orient(frame)
        elif idx:
            return self.body_poses[frame, idx, :3]
        else:
            return np.zeros([3], dtype=np.float32)

    def get_bone_rotation(self, bone_name: str, frame=0) -> spRotation:
        rotvec = self.get_bone_rotvec(bone_name, frame)
        return spRotation.from_rotvec(rotvec)  # type: ignore

    def get_bone_matrix_basis(self, bone_name: str, frame=0) -> np.ndarray:
        """pose2rest: relative to the bone space at rest pose.

        Result:
            np.ndarray: transform matrix like
                [
                    [R, T],
                    [0, 1]
                ]
        """
        idx = self._bone2idx(bone_name)
        if idx == 0:
            transl = self.get_transl(frame)
        else:
            transl = np.zeros(3)
        rot = self.get_bone_rotation(bone_name, frame)
        matrix_basis = rot.as_matrix()
        matrix_basis = np.pad(matrix_basis, (0, 1))
        matrix_basis[:3, 3] = transl
        matrix_basis[3, 3] = 1
        return matrix_basis

    def get_parent_bone_name(self, bone_name: str) -> Optional[str]:
        ...

    def convert_fps_smplx_data(self, smplx_data: Dict[str, np.ndarray], scaling: int) -> Dict[str, np.ndarray]:
        for key, value in smplx_data.items():
            if key in ['betas']:
                continue
            smplx_data[key] = value[::scaling, :]
        return smplx_data

    def convert_fps(self, fps: float):
        """Converts the frames per second (fps) of the animation to the specified value.

        Args:
            fps (float): The desired frames per second.

        Raises:
            NotImplementedError:
                - If the desired fps is greater than the current fps, motion interpolation is not supported.
                - If the desired fps is less than the current fps, motion interpolation is not supported.
        """
        if fps == self.fps:
            return

        scaling = self.fps / fps
        if scaling - int(scaling) <= 1e-7:
            scaling = int(scaling)
            self.transl = self.transl[::scaling, :]
            self.body_poses = self.body_poses[::scaling, :, :]
            self.global_orient: np.ndarray = self.global_orient[::scaling, :]
            self.n_frames = self.body_poses.shape[0]
            if hasattr(self, 'smpl_data'):
                self.smpl_data = self.convert_fps_smplx_data(self.smpl_data, scaling)
            if hasattr(self, 'smplx_data'):
                self.smplx_data = self.convert_fps_smplx_data(self.smplx_data, scaling)
            self.fps = fps
        elif fps > self.fps:
            # TODO: motion interpolation
            raise NotImplementedError(f'Not support up sampling from {self.fps}fps to {fps}fps')
        else:
            # TODO: motion interpolation
            raise NotImplementedError(f'Not support down sampling from {self.fps}fps to {fps}fps')

    def slice_motion(self, frame_interval: int):
        """Slice the motion sequence by a given frame interval.

        Args:
            frame_interval (int): The frame interval to use for slicing the motion sequence.
        """
        assert isinstance(frame_interval, int), TypeError(f'scaling={frame_interval} should be int')

        self.transl = self.transl[::frame_interval, :]
        self.body_poses = self.body_poses[::frame_interval, :, :]
        self.global_orient: np.ndarray = self.global_orient[::frame_interval, :]
        self.n_frames = self.body_poses.shape[0]
        if hasattr(self, 'smpl_data'):
            self.smpl_data = self.convert_fps_smplx_data(self.smpl_data, frame_interval)
        if hasattr(self, 'smplx_data'):
            self.smplx_data = self.convert_fps_smplx_data(self.smplx_data, frame_interval)

    def sample_motion(self, n_frames: int):
        """Randomly sample motions, picking n_frames from the original motion sequence.
        The indices are totally random using `np.random.choice`.

        Args:
            n_frames (int): The number of frames to sample. Randomly sampled from the original motion sequence.
        """
        assert n_frames > 0, f'n_frames={n_frames}'
        if n_frames == self.n_frames:
            return

        indices = np.random.choice(self.n_frames, size=n_frames)
        self.transl = self.transl[indices]
        self.body_poses = self.body_poses[indices]
        self.global_orient = self.global_orient[indices]
        self.n_frames = n_frames
        if hasattr(self, 'smpl_data'):
            for k, v in self.smpl_data.items():
                if k != 'betas':
                    self.smpl_data[k] = v[indices]
        if hasattr(self, 'smplx_data'):
            for k, v in self.smplx_data.items():
                if k != 'betas':
                    self.smplx_data[k] = v[indices]
        self.insert_rest_pose()

    def cut_transl(self):
        """Cut the transl to zero.

        This will make the animation stay in place, like root motion.
        """
        self.transl = np.zeros_like(self.transl)
        if hasattr(self, 'smpl_data'):
            self.smpl_data['transl'] = np.zeros_like(self.smpl_data['transl'])
        if hasattr(self, 'smplx_data'):
            self.smplx_data['transl'] = np.zeros_like(self.smplx_data['transl'])

    def insert_rest_pose(self):
        """Insert rest pose to the first frame."""
        self.transl = np.insert(self.transl, 0, 0, axis=0)
        self.body_poses = np.insert(self.body_poses, 0, 0, axis=0)
        self.global_orient = np.insert(self.global_orient, 0, 0, axis=0)
        self.n_frames += 1
        if hasattr(self, 'smpl_data'):
            for key, arr in self.smpl_data.items():
                if key == 'betas':
                    continue
                self.smpl_data[key] = np.insert(arr, 0, 0, axis=0)
        if hasattr(self, 'smplx_data'):
            for key, arr in self.smplx_data.items():
                if key == 'betas':
                    continue
                self.smplx_data[key] = np.insert(arr, 0, 0, axis=0)

    def get_motion_data(self) -> List[Dict[str, Dict[str, List[float]]]]:
        """Returns a list of dictionaries containing `rotation` and `location` for each
        bone of each frame in the animation.

        Each dictionary contains bone names as keys and a nested dictionary as values. The nested dictionary contains
        'rotation' and 'location' keys, which correspond to the rotation and location of the bone in that frame.

        Returns:
            List[Dict[str, Dict[str, List[float]]]]: A list of dictionaries containing motion data for each frame of the animation.
        """
        motion_data: List[Dict[str, Dict[str, List[float]]]] = []
        for frame in range(self.n_frames):
            frame_motion_data = {}
            for bone_name in self.BONE_NAMES:
                mat_basis = Matrix(self.get_bone_matrix_basis(bone_name, frame))
                loc_, quat_, _ = mat_basis.decompose()
                # equal to ==> transform = frame_motion_data[tgt_bone_name]
                transform = frame_motion_data.setdefault(bone_name, {})
                transform['rotation'] = quat_.tolist()
                if self.BONE_NAME_TO_IDX[bone_name] == 0:  # pelvis bone
                    transform['location'] = loc_.tolist()
            motion_data.append(frame_motion_data)
        return motion_data

    def __repr__(self) -> str:
        return f'Motion(n_frames={self.n_frames}, fps={self.fps})'


class SMPLMotion(Motion):
    SMPL_IDX_TO_NAME: Dict[int, str] = OrderedDict(SMPL_IDX_TO_JOINTS)
    NAME_TO_SMPL_IDX = OrderedDict([(v, k) for k, v in SMPL_IDX_TO_NAME.items() if v])
    NAMES = [x for x in SMPL_IDX_TO_NAME.values() if x]
    PARENTS = list(SMPL_PARENT_IDX)
    BONE_NAMES = SMPLX_JOINT_NAMES[1 : NUM_SMPLX_BODYJOINTS + 1]
    BONE_NAME_TO_IDX: Dict[str, int] = {bone_name: idx for idx, bone_name in enumerate(BONE_NAMES)}

    # In order to make the smpl head up to +z
    GLOBAL_ORIENT_ADJUSTMENT = spRotation.from_euler('xyz', np.deg2rad([180, 0, 0]))

    def __init__(
        self,
        transl: np.ndarray,
        body_poses: np.ndarray,
        n_frames: Optional[int] = None,
        fps: float = 30.0,
    ) -> None:
        super().__init__(transl, body_poses, n_frames=n_frames, fps=fps)
        self.smpl_data: Dict[str, np.ndarray]

    @classmethod
    def from_smpl_data(
        cls,
        smpl_data: Dict[str, np.ndarray],
        fps: float = 30.0,
        insert_rest_pose: bool = False,
        global_orient_adj: Optional[spRotation] = GLOBAL_ORIENT_ADJUSTMENT,
        vector_convertor: Optional[ConverterType] = Converter.vec_humandata2smplx,
    ) -> Self:
        """Create SMPLMotion instance from smpl_data.

        `smpl_data` should be a dict like object,
        with required keys:
            ["body_pose", "global_orient"]
        and optional key:
            ["transl"].

        Args:
            smpl_data: dict with require keys ["body_pose", "global_orient"]
                and optional key ["transl"]
            insert_rest_pose (bool):
                whether to insert a rest pose at the 0th-frame.

        Returns:
            SMPLMotion: An instance of SMPLMotion containing the smpl_data.
        """
        smpl_data = dict(smpl_data)
        _get_smpl = partial(_get_from_smpl_x_, smpl_x_data=smpl_data, dtype=np.float32)

        n_frames = smpl_data['body_pose'].shape[0]
        betas = _get_smpl('betas', shape=[1, 10])
        transl = _get_smpl('transl', shape=[n_frames, 3], required=False)
        global_orient = _get_smpl('global_orient', shape=[n_frames, 3])
        body_pose = _get_smpl('body_pose', shape=[n_frames, -1])
        if body_pose.shape[1] == 63:
            body_pose = np.concatenate([body_pose, np.zeros([n_frames, 6])], axis=1)
        assert body_pose.shape[1] == 69, f'body_pose.shape={body_pose.shape}'
        # Insert the 0 frame as a T-Pose
        smpl_data = {
            'betas': betas,
            'transl': transl,
            'global_orient': global_orient,
            'body_pose': body_pose,
        }
        if insert_rest_pose:
            for key, arr in smpl_data.items():
                if key != 'betas':
                    arr = np.insert(arr, 0, 0, axis=0)
                    smpl_data[key] = arr

        # Create instance
        transl_bl = smpl_data['transl']
        n_frames = transl_bl.shape[0]
        body_poses_bl = np.concatenate(
            [smpl_data[key] for key in ('global_orient', 'body_pose')],
            axis=1,
            dtype=np.float32,
        ).reshape([n_frames, -1, 3])
        # - Adjust in order to make the smpl head up to +z
        if global_orient_adj is not None:
            body_poses_bl[:, 0, :] = (global_orient_adj * spRotation.from_rotvec(body_poses_bl[:, 0, :])).as_rotvec()
            if insert_rest_pose:
                body_poses_bl[0, 0, :] = 0.0

        # - Convert from humandata to smplx pelvis local space in blender
        if vector_convertor is not None:
            transl_bl = vector_convertor(transl_bl)
            smpl_data['transl'] = transl_bl

        instance = cls(transl=transl_bl, body_poses=body_poses_bl, fps=fps)
        instance.smpl_data = smpl_data
        return instance

    def get_bone_rotvec(self, bone_name, frame=0) -> np.ndarray:
        idx = self._bone2idx(bone_name)
        if idx == 0:
            return self.get_global_orient(frame)
        elif idx:
            return self.body_poses[frame, idx, :3]
        else:
            return np.zeros([3], dtype=np.float32)

    def get_parent_bone_name(self, bone_name) -> Optional[str]:
        idx = self._bone2idx(bone_name)
        if idx is None:
            raise ValueError(f'bone.name="{bone_name}" not in smpl skeleton.')
        else:
            parent_idx = self.PARENTS[idx]
            if parent_idx == -1:
                return None
            else:
                return self.BONE_NAMES[parent_idx]

    def dump_humandata(
        self,
        filepath: PathLike,
        betas: np.ndarray,
        meta: Optional[Dict[str, Any]] = None,
        global_orient_offset: np.ndarray = np.zeros(3),
        transl_offset: np.ndarray = np.zeros(3),
        root_location_t0: Optional[np.ndarray] = None,
        pelvis_location_t0: Optional[np.ndarray] = None,
    ) -> None:
        """Dump the motion data to a humandata file at the given `filepath`.

        HumanData is a structure of smpl/smplx data defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md

        The humandata file is a npz file containing the following keys:
        ```
        motion_data = {
            '__data_len__': n_frames,
            'smpl': {
                'betas': betas,  # (1, 10)
                'transl': transl,  # (n_frames, 3)
                'global_orient': global_orient,  # (n_frames, 3)
                'body_pose': body_pose,  # (n_frames, 69)
            },
            'meta': {'gender': 'neutral'},  # optional
        }
        ```

        Args:
            filepath (PathLike): The filepath to dump the motion data to.
            betas (np.ndarray): The betas array.
            meta (Optional[Dict[str, Any]]): Additional metadata. Defaults to None.
            global_orient_offset (np.ndarray): The global orientation offset. Defaults to np.zeros(3).
            transl_offset (np.ndarray): The translation offset. Defaults to np.zeros(3).
            root_location_t0 (Optional[np.ndarray]): The root location at time 0. Defaults to None.
            pelvis_location_t0 (Optional[np.ndarray]): The pelvis location at time 0. Defaults to None.
        """
        humandata = get_humandata(
            smpl_x_data=self.smplx_data,
            smpl_x_type='smpl',
            betas=betas,
            meta=meta,
            global_orient_offset=global_orient_offset,
            transl_offset=transl_offset,
            root_location_t0=root_location_t0,
            pelvis_location_t0=pelvis_location_t0,
        )
        filepath = Path(filepath).resolve()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        np.savez(filepath, **humandata)

    def __repr__(self) -> str:
        return f'SMPLMotion(n_frames={self.n_frames}, fps={self.fps})'


class SMPLXMotion(Motion):
    SMPLX_IDX_TO_NAME: Dict[int, str] = OrderedDict(SMPLX_IDX_TO_JOINTS)
    NAME_TO_SMPL_IDX = OrderedDict([(v, k) for k, v in SMPLX_IDX_TO_NAME.items() if v])
    NAMES = [x for x in SMPLX_IDX_TO_NAME.values() if x]
    PARENTS = list(SMPLX_PARENT_IDX)
    BONE_NAMES = SMPLX_JOINT_NAMES
    BONE_NAME_TO_IDX: Dict[str, int] = {bone_name: idx for idx, bone_name in enumerate(BONE_NAMES)}

    # In order to make the smpl head up to +z
    GLOBAL_ORIENT_ADJUSTMENT = spRotation.from_euler('xyz', np.deg2rad([180, 0, 0]))

    def __init__(
        self,
        transl: np.ndarray,
        body_poses: np.ndarray,
        n_frames: Optional[int] = None,
        fps: float = 30.0,
    ) -> None:
        super().__init__(transl, body_poses, n_frames=n_frames, fps=fps)
        self.smplx_data: Dict[str, np.ndarray]

    @classmethod
    def from_smplx_data(
        cls,
        smplx_data: Dict[str, np.ndarray],
        fps: float = 30.0,
        insert_rest_pose: bool = False,
        flat_hand_mean: bool = False,
        global_orient_adj: Optional[spRotation] = GLOBAL_ORIENT_ADJUSTMENT,
        vector_convertor: Optional[Callable[[np.ndarray], np.ndarray]] = Converter.vec_humandata2smplx,
    ) -> Self:
        """Create SMPLXMotion instance from smplx_data.

        `smplx_data` should be a dict like object,
        with required keys:
            ["body_pose", "global_orient"]
        and optional key:
            ["transl"]

        Args:
            smplx_data: require keys ["body_pose", "global_orient"]
                and optional key ["transl"]
            fps (float): the motion's FPS. Defaults to 30.0.
            insert_rest_pose (bool):
                whether to insert a rest pose at the 0th-frame.
                Defaults to False.
            flat_hand_mean (bool):
                whether the hands with zero rotations are flat hands.
                Defaults to False.
            global_orient_adj (spRotation, None):
            vector_convertor: a function applies to smplx_data's translation.

        Returns:
            SMPLXMotion: An instance of SMPLXMotion containing the smplx_data.
        """
        smplx_data = dict(smplx_data)
        _get_smplx = partial(_get_from_smpl_x_, smpl_x_data=smplx_data, dtype=np.float32)
        n_frames = smplx_data['body_pose'].shape[0]
        betas = _get_smplx('betas', shape=[1, 10])
        transl = _get_smplx('transl', shape=[n_frames, 3], required=False)
        global_orient = _get_smplx('global_orient', shape=[n_frames, 3])
        body_pose = _get_smplx('body_pose', shape=[n_frames, 63])
        jaw_pose = _get_smplx('jaw_pose', shape=[n_frames, 3], required=False)
        leye_pose = _get_smplx('leye_pose', shape=[n_frames, 3], required=False)
        reye_pose = _get_smplx('reye_pose', shape=[n_frames, 3], required=False)
        left_hand_pose = _get_smplx('left_hand_pose', shape=[n_frames, 45], required=False)
        right_hand_pose = _get_smplx('right_hand_pose', shape=[n_frames, 45], required=False)
        expression = _get_smplx('expression', shape=[n_frames, 10], required=False)

        # Insert the 0 frame as a T-Pose
        smplx_data = {
            'betas': betas,
            'transl': transl,
            'global_orient': global_orient,
            'body_pose': body_pose,
            'left_hand_pose': left_hand_pose,
            'right_hand_pose': right_hand_pose,
            'jaw_pose': jaw_pose,
            'leye_pose': leye_pose,
            'reye_pose': reye_pose,
            'expression': expression,
        }
        if insert_rest_pose:
            for key, arr in smplx_data.items():
                if key != 'betas':
                    arr = np.insert(arr, 0, 0, axis=0)
                    smplx_data[key] = arr

        # Create instance
        transl_bl = smplx_data['transl']
        # hand relax pose
        if not flat_hand_mean:
            left_hand_relax_pose = np.array(SMPLX_HAND_POSES['relaxed'][0]).reshape(45)
            right_hand_relax_pose = np.array(SMPLX_HAND_POSES['relaxed'][1]).reshape(45)
            smplx_data['left_hand_pose'] += left_hand_relax_pose
            smplx_data['right_hand_pose'] += right_hand_relax_pose
        # - Adjust in order to make the smpl head up to +z
        if global_orient_adj is not None:
            global_orient_bl = spRotation.from_rotvec(smplx_data['global_orient'])
            smplx_data['global_orient'] = (global_orient_adj * global_orient_bl).as_rotvec()
            if insert_rest_pose:
                smplx_data['global_orient'][0] = 0
        # - Convert from humandata to smplx pelvis local space in blender
        if vector_convertor is not None:
            transl_bl = vector_convertor(transl_bl)
            smplx_data['transl'] = transl_bl

        # Concatenate all the poses
        body_pose_keys = (
            'global_orient',
            'body_pose',
            'jaw_pose',
            'leye_pose',
            'reye_pose',
            'left_hand_pose',
            'right_hand_pose',
        )
        body_poses_bl = [smplx_data[key] for key in body_pose_keys]
        n_frames = transl_bl.shape[0]
        body_poses_bl = np.concatenate(body_poses_bl, axis=1, dtype=np.float32).reshape([n_frames, -1, 3])

        instance = SMPLXMotion(transl=transl_bl, body_poses=body_poses_bl, fps=fps)
        instance.smplx_data = smplx_data
        return instance

    @classmethod
    def from_amass_data(cls, amass_data, insert_rest_pose: bool, flat_hand_mean: bool = True) -> Self:
        """Create a Motion instance from AMASS data (SMPLX)

        Args:
            amass_data (dict): A dictionary containing the AMASS data.
            insert_rest_pose (bool): Whether to insert a rest pose at the beginning of the motion.
            flat_hand_mean (bool): Whether to use the flat hand mean pose.

        Returns:
            SMPLXMotion: A SMPLXMotion instance containing the AMASS data.

        Raises:
            AssertionError: If the surface model type in the AMASS data is not 'smplx'.
        """
        assert amass_data['surface_model_type'] == 'smplx', f"surface_model_type={amass_data['surface_model_type']}"
        fps = amass_data['mocap_frame_rate']

        betas = amass_data['betas'][:10]
        transl = amass_data['trans']
        global_orient = amass_data['root_orient']
        body_pose = amass_data['pose_body']
        left_hand_pose = amass_data['pose_hand'][:, :45]
        right_hand_pose = amass_data['pose_hand'][:, 45:]
        jaw_pose = amass_data['pose_jaw']
        leye_pose = amass_data['pose_eye'][:, :3]
        reye_pose = amass_data['pose_eye'][:, 3:]
        n_frames = global_orient.shape[0]
        expression = np.zeros([n_frames, 10], dtype=np.float32)

        # motions in AMASS dataset are -y up, rotate it to +y up
        amass2humandata_adj = spRotation.from_euler('xyz', np.deg2rad([90, 180, 0]))
        global_orient = (amass2humandata_adj * spRotation.from_rotvec(global_orient)).as_rotvec()  # type: ignore
        # transl_0 = transl[0, :]
        # transl = amass2humandata_adj.apply(transl - transl_0) + transl_0
        transl = Converter.vec_amass2humandata(transl)
        # TODO: all axis offset
        height_offset = transl[0, 1]

        smplx_data = {
            'betas': betas,
            'transl': transl,
            'global_orient': global_orient,
            'body_pose': body_pose,
            'left_hand_pose': left_hand_pose,
            'right_hand_pose': right_hand_pose,
            'jaw_pose': jaw_pose,
            'leye_pose': leye_pose,
            'reye_pose': reye_pose,
            'expression': expression,
        }
        if insert_rest_pose:
            for key, arr in smplx_data.items():
                arr = arr.astype(np.float32)
                if key != 'betas':
                    arr = np.insert(arr, 0, 0, axis=0)
                    if key == 'global_orient':
                        # make 0-th frame has the same orient with humandata
                        arr[0, :] = [np.pi, 0, 0]
                    elif key == 'transl':
                        arr[1:, 1] -= height_offset
                        # TODO: handle pelvis height, get pelvis_height, and set frame-0 as T-pose
                        # arr[0, 1] = pelvis_height
                smplx_data[key] = arr

        return cls.from_smplx_data(smplx_data, insert_rest_pose=False, fps=fps, flat_hand_mean=flat_hand_mean)

    def get_parent_bone_name(self, bone_name) -> Optional[str]:
        idx = self._bone2idx(bone_name)
        if idx is None:
            raise ValueError(f'bone.name="{bone_name}" not in smplx skeleton.')
        else:
            parent_idx = self.PARENTS[idx]
            if parent_idx == -1:
                return None
            else:
                return self.BONE_NAMES[parent_idx]

    def dump_humandata(
        self,
        filepath: PathLike,
        betas: np.ndarray,
        meta: Optional[Dict[str, Any]] = None,
        global_orient_offset: np.ndarray = np.zeros(3),
        transl_offset: np.ndarray = np.zeros(3),
        root_location_t0: Optional[np.ndarray] = None,
        pelvis_location_t0: Optional[np.ndarray] = None,
    ) -> None:
        """Dump the motion data to a humandata file at the given `filepath`.

        HumanData is a structure of smpl/smplx data defined in https://github.com/open-mmlab/mmhuman3d/blob/main/docs/human_data.md

        The humandata file is a npz file containing the following keys:
        ```python
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
        ```

        Args:
            filepath (PathLike): The filepath to dump the motion data to.
            betas (np.ndarray): The betas array.
            meta (Optional[Dict[str, Any]]): Additional metadata. Defaults to None.
            global_orient_offset (np.ndarray): The global orientation offset. Defaults to np.zeros(3).
            transl_offset (np.ndarray): The translation offset. Defaults to np.zeros(3).
            root_location_t0 (Optional[np.ndarray]): The root location at time 0. Defaults to None.
            pelvis_location_t0 (Optional[np.ndarray]): The pelvis location at time 0. Defaults to None.
        """
        humandata = get_humandata(
            smpl_x_data=self.smplx_data,
            smpl_x_type='smplx',
            betas=betas,
            meta=meta,
            global_orient_offset=global_orient_offset,
            transl_offset=transl_offset,
            root_location_t0=root_location_t0,
            pelvis_location_t0=pelvis_location_t0,
        )
        filepath = Path(filepath).resolve()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        np.savez(filepath, **humandata)

    def __repr__(self) -> str:
        return f'SMPLXMotion(n_frames={self.n_frames}, fps={self.fps})'


def _get_from_smpl_x_(key, shape, *, smpl_x_data, dtype=np.float32, required=True) -> np.ndarray:
    """Get data from smpl-x data dict.

    Args:
        key: key in smpl_x_data
        shape: shape of the data, [n_frames, n_dims]
        smpl_x_data: smpl-x data dict
        dtype: data type
        required: whether the key is required

    Returns:
        data: data with shape [n_frames, n_dims]
    """
    if (required or key in smpl_x_data) and smpl_x_data[key].size > 0:
        _data = smpl_x_data[key].astype(dtype)
        n_frames, n_dims = shape
        _data = _data.reshape([n_frames, -1])
        if not n_dims < 0:
            _data = _data[:, :n_dims]  # XXX: handle the case that n_dims > data.shape[1]
        return _data
    return np.zeros(shape, dtype=dtype)


def _transform_transl_global_orient_(
    global_orient: np.ndarray,
    transl: np.ndarray,
    global_orient_offset: np.ndarray,
    transl_offset: np.ndarray,
    root_location_t0: Optional[np.ndarray] = None,
    pelvis_location_t0: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Transform the global orientation and translation based on the given offsets.

    Args:
        global_orient (np.ndarray): Global orientation array.
        transl (np.ndarray): Translation array.
        global_orient_offset (np.ndarray): Global orientation offset array.
        transl_offset (np.ndarray): Translation offset array.
        root_location_t0 (Optional[np.ndarray]): Root location at time 0. Defaults to None.
        pelvis_location_t0 (Optional[np.ndarray]): Pelvis location at time 0. Defaults to None.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Transformed global orientation and translation arrays.
    """
    R_offset = spRotation.from_rotvec(global_orient_offset) * spRotation.from_rotvec(global_orient[0, :]).inv()
    global_orient_ = (R_offset * spRotation.from_rotvec(global_orient)).as_rotvec()

    loc0 = transl[0, :]

    if pelvis_location_t0 is not None and root_location_t0 is not None:
        transl_offset_t0 = pelvis_location_t0 - root_location_t0
        rot_pivot_offset = transl_offset_t0 + transl_offset - loc0
        transl_ = R_offset.apply(transl + rot_pivot_offset) - pelvis_location_t0
    else:
        transl_ = transl + transl_offset - loc0

    return global_orient_, transl_


def get_humandata(
    smpl_x_data: Dict[str, np.ndarray],
    smpl_x_type: Literal['smpl', 'smplx'],
    betas: np.ndarray,
    meta: Optional[Dict[str, Any]] = None,
    global_orient_offset: np.ndarray = np.zeros(3),
    transl_offset: np.ndarray = np.zeros(3),
    root_location_t0: Optional[np.ndarray] = None,
    pelvis_location_t0: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Get human data for a given set of parameters.

    Args:
        smpl_x_data (Dict[str, np.ndarray]): Dictionary containing the SMPL-X data.
        smpl_x_type (Literal['smpl', 'smplx']): Type of SMPL-X model.
        betas (np.ndarray): Array of shape (n, 10) representing the shape parameters.
        meta (Optional[Dict[str, Any]], optional): Additional metadata. Defaults to None.
        global_orient_offset (np.ndarray): Array of shape (n, 3) representing the global orientation offset.
        transl_offset (np.ndarray): Array of shape (3,) representing the translation offset.
        root_location_t0 (Optional[np.ndarray], optional): Array of shape (3,) representing the root location at time t=0. Defaults to None.
        pelvis_location_t0 (Optional[np.ndarray], optional): Array of shape (3,) representing the pelvis location at time t=0. Defaults to None.

    Returns:
        dict: Dictionary containing the human data.
    """
    global_orient = smpl_x_data['global_orient'].reshape(-1, 3)
    n = global_orient.shape[0]
    transl = smpl_x_data['transl'].reshape(n, 3)
    body_pose = smpl_x_data['body_pose'].reshape(n, -1)
    bone_len = body_pose.shape[1]
    assert n > 0, f'Got n_frames={n}, should be > 0.'
    assert bone_len in (63, 69), f'Got body_pose in [{n}, {bone_len}], should be in shape of [n, 63] or [n, 69].'

    # transform
    global_orient_, transl_ = _transform_transl_global_orient_(
        global_orient=global_orient,
        transl=transl,
        global_orient_offset=global_orient_offset,
        transl_offset=transl_offset,
        root_location_t0=root_location_t0,
        pelvis_location_t0=pelvis_location_t0,
    )

    if smpl_x_type == 'smpl':
        if bone_len == 69:
            body_pose_ = body_pose
        elif bone_len == 63:
            body_pose_ = np.concatenate([body_pose, np.zeros([n, 6])], axis=1, dtype=np.float32)
    else:
        body_pose_ = body_pose[:, :63]

    smpl_x_data_ = {
        'betas': betas.astype(np.float32),
        'global_orient': global_orient_.astype(np.float32),
        'transl': transl_.astype(np.float32),
        'body_pose': body_pose_.astype(np.float32),
    }

    if smpl_x_type == 'smplx':
        extra = {
            'left_hand_pose': np.zeros([n, 45], dtype=np.float32),
            'right_hand_pose': np.zeros([n, 45], dtype=np.float32),
            'jaw_pose': np.zeros([n, 3], dtype=np.float32),
            'leye_pose': np.zeros([n, 3], dtype=np.float32),
            'reye_pose': np.zeros([n, 3], dtype=np.float32),
            'expression': np.zeros([n, 10], dtype=np.float32),
        }
        for k, v in extra.items():
            if k in smpl_x_data:
                extra[k] = smpl_x_data[k].reshape(v.shape).astype(np.float32)
        smpl_x_data_.update(extra)

    humandata = {
        '__data_len__': global_orient_.shape[0],
        smpl_x_type: smpl_x_data_,
        'meta': meta,
    }
    return humandata
