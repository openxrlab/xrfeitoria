from collections import OrderedDict
from functools import partial
from typing import Callable, Dict, List, Optional

import numpy as np
from scipy.spatial.transform import Rotation as spRotation
from typing_extensions import Self

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

    def convert_fps(self, fps):
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
        """Randomly sample motion to n_frames."""
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
        """Cut the transl to zero."""
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
                self.smplx_dat[key] = np.insert(arr, 0, 0, axis=0)
        if hasattr(self, 'smplx_data'):
            for key, arr in self.smplx_data.items():
                if key == 'betas':
                    continue
                self.smplx_data[key] = np.insert(arr, 0, 0, axis=0)

    def get_motion_data(self) -> List[Dict[str, Dict[str, List[float]]]]:
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


class SMPLMotion(Motion):
    SMPL_IDX_TO_NAME: Dict[int, str] = OrderedDict(SMPL_IDX_TO_JOINTS)
    NAME_TO_SMPL_IDX = OrderedDict([(v, k) for k, v in SMPL_IDX_TO_NAME.items() if v])
    NAMES = [x for x in SMPL_IDX_TO_NAME.values() if x]
    PARENTS = list(SMPL_PARENT_IDX)
    BONE_NAMES = SMPLX_JOINT_NAMES[:NUM_SMPLX_BODYJOINTS]
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
            Self: _description_
        """
        smpl_data = dict(smpl_data)
        _get_smpl = partial(_get_from_smpl_x, smpl_x_data=smpl_data, dtype=np.float32)

        n_frames = smpl_data['body_pose'].shape[0]
        betas = _get_smpl('betas', shape=[10])
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
        """Create SMPLXMotion instance from smpl_data.

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
            Self: _description_
        """
        smplx_data = dict(smplx_data)
        _get_smplx = partial(_get_from_smpl_x, smpl_x_data=smplx_data, dtype=np.float32)
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
    def from_amass_data(cls, amass_data, insert_rest_pose: bool):
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

        return cls.from_smplx_data(
            smplx_data,
            insert_rest_pose=False,
            fps=fps,
            flat_hand_mean=True,
        )

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


def _get_from_smpl_x(key, shape, *, smpl_x_data, dtype=np.float32, required=True) -> np.ndarray:
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
        _data = _data[:, :n_dims]  # XXX: handle the case that n_dims > data.shape[1]
        return _data
    return np.zeros(shape, dtype=dtype)
    return np.zeros(shape, dtype=dtype)
