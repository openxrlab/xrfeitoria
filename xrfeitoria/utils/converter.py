"""Converter for different spaces."""

from typing import Union

import numpy as np

from ..data_structure.constants import Vector


def rotation_matrix(angles: Union[Vector, np.ndarray], order='xyz', degrees: bool = True) -> np.ndarray:
    """
    Args:
        angles (Tuple[float, float, float]): Rotation angles in degrees or radians.
        order (str, optional): Rotation order. Defaults to 'xyz'.
        degrees (bool, optional): Whether the input angles are in degrees. Defaults to True.
    Returns:
        ndarray: Rotation matrix 3x3.

    Examples:
        >>> rotation_matrix((0, 0, 0), order='xyz')

    References:
        https://programming-surgeon.com/en/euler-angle-python-en/
    """
    if degrees:
        angles = np.deg2rad(angles)

    theta1, theta2, theta3 = angles
    c1 = np.cos(theta1)
    s1 = np.sin(theta1)
    c2 = np.cos(theta2)
    s2 = np.sin(theta2)
    c3 = np.cos(theta3)
    s3 = np.sin(theta3)

    if order == 'xzx':
        matrix = np.array(
            [
                [c2, -c3 * s2, s2 * s3],
                [c1 * s2, c1 * c2 * c3 - s1 * s3, -c3 * s1 - c1 * c2 * s3],
                [s1 * s2, c1 * s3 + c2 * c3 * s1, c1 * c3 - c2 * s1 * s3],
            ]
        )
    elif order == 'xyx':
        matrix = np.array(
            [
                [c2, s2 * s3, c3 * s2],
                [s1 * s2, c1 * c3 - c2 * s1 * s3, -c1 * s3 - c2 * c3 * s1],
                [-c1 * s2, c3 * s1 + c1 * c2 * s3, c1 * c2 * c3 - s1 * s3],
            ]
        )
    elif order == 'yxy':
        matrix = np.array(
            [
                [c1 * c3 - c2 * s1 * s3, s1 * s2, c1 * s3 + c2 * c3 * s1],
                [s2 * s3, c2, -c3 * s2],
                [-c3 * s1 - c1 * c2 * s3, c1 * s2, c1 * c2 * c3 - s1 * s3],
            ]
        )
    elif order == 'yzy':
        matrix = np.array(
            [
                [c1 * c2 * c3 - s1 * s3, -c1 * s2, c3 * s1 + c1 * c2 * s3],
                [c3 * s2, c2, s2 * s3],
                [-c1 * s3 - c2 * c3 * s1, s1 * s2, c1 * c3 - c2 * s1 * s3],
            ]
        )
    elif order == 'zyz':
        matrix = np.array(
            [
                [c1 * c2 * c3 - s1 * s3, -c3 * s1 - c1 * c2 * s3, c1 * s2],
                [c1 * s3 + c2 * c3 * s1, c1 * c3 - c2 * s1 * s3, s1 * s2],
                [-c3 * s2, s2 * s3, c2],
            ]
        )
    elif order == 'zxz':
        matrix = np.array(
            [
                [c1 * c3 - c2 * s1 * s3, -c1 * s3 - c2 * c3 * s1, s1 * s2],
                [c3 * s1 + c1 * c2 * s3, c1 * c2 * c3 - s1 * s3, -c1 * s2],
                [s2 * s3, c3 * s2, c2],
            ]
        )
    elif order == 'xyz':
        matrix = np.array(
            [
                [c2 * c3, -c2 * s3, s2],
                [c1 * s3 + c3 * s1 * s2, c1 * c3 - s1 * s2 * s3, -c2 * s1],
                [s1 * s3 - c1 * c3 * s2, c3 * s1 + c1 * s2 * s3, c1 * c2],
            ]
        )
    elif order == 'xzy':
        matrix = np.array(
            [
                [c2 * c3, -s2, c2 * s3],
                [s1 * s3 + c1 * c3 * s2, c1 * c2, c1 * s2 * s3 - c3 * s1],
                [c3 * s1 * s2 - c1 * s3, c2 * s1, c1 * c3 + s1 * s2 * s3],
            ]
        )
    elif order == 'yxz':
        matrix = np.array(
            [
                [c1 * c3 + s1 * s2 * s3, c3 * s1 * s2 - c1 * s3, c2 * s1],
                [c2 * s3, c2 * c3, -s2],
                [c1 * s2 * s3 - c3 * s1, c1 * c3 * s2 + s1 * s3, c1 * c2],
            ]
        )
    elif order == 'yzx':
        matrix = np.array(
            [
                [c1 * c2, s1 * s3 - c1 * c3 * s2, c3 * s1 + c1 * s2 * s3],
                [s2, c2 * c3, -c2 * s3],
                [-c2 * s1, c1 * s3 + c3 * s1 * s2, c1 * c3 - s1 * s2 * s3],
            ]
        )
    elif order == 'zyx':
        matrix = np.array(
            [
                [c1 * c2, c1 * s2 * s3 - c3 * s1, s1 * s3 + c1 * c3 * s2],
                [c2 * s1, c1 * c3 + s1 * s2 * s3, c3 * s1 * s2 - c1 * s3],
                [-s2, c2 * s3, c2 * c3],
            ]
        )
    elif order == 'zxy':
        matrix = np.array(
            [
                [c1 * c3 - s1 * s2 * s3, -c2 * s1, c1 * s3 + c3 * s1 * s2],
                [c3 * s1 + c1 * s2 * s3, c1 * c2, s1 * s3 - c1 * c3 * s2],
                [-c2 * s3, s2, c2 * c3],
            ]
        )

    return matrix


class ConverterMotion:
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
        if isinstance(vector, list):
            vector = np.array(vector)
        if vector.shape == (3,):
            ret = np.array([vector[0], -vector[1], -vector[2]], dtype=vector.dtype)
        elif vector.ndim == 2 and vector.shape[1] == 3:
            ret = np.array([vector[:, 0], -vector[:, 1], -vector[:, 2]]).T
        else:
            raise ValueError(f'vector.shape={vector.shape}')
        return ret

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
        if isinstance(vector, list):
            vector = np.array(vector)
        if vector.shape == (3,):
            vector = np.array([-vector[0], -vector[2], -vector[1]], dtype=vector.dtype)
        elif vector.ndim == 2 and vector.shape[1] == 3:
            vector = np.array([-vector[:, 0], -vector[:, 2], -vector[:, 1]]).T
        else:
            raise ValueError(f'vector.shape={vector.shape}')
        return vector


class ConverterUnreal:
    units_scale = 100.0  # 1 meter = 100 cm

    @classmethod
    def rotation_camera_from_ue(cls, euler, degrees=True) -> np.ndarray:
        """Convert from ue camera space to opencv camera space convention.
        Note: convert to left-handed

        Args:
            euler (np.ndarray): of shape (3,)
            degrees (bool, optional): Whether the input angles are in degrees. Defaults to True.

        Returns:
            np.ndarray: Rotation matrix 3x3.
        """
        x, y, z = -euler[1], -euler[2], -euler[0]
        return rotation_matrix([x, y, z], order='xyz', degrees=degrees)

    @classmethod
    def rotation_from_ue(cls, euler, degrees=True) -> np.ndarray:
        """Convert from ue camera space to opencv camera space convention.

        Args:
            euler (np.ndarray): of shape (3,)
            offset (np.ndarray, optional): of shape (3,). Defaults to ROTATION_OFFSET [0, 0, -90.0].
            degrees (bool, optional): Whether the input angles are in degrees. Defaults to True.

        Returns:
            np.ndarray: Rotation matrix 3x3.
        """
        from scipy.spatial.transform import Rotation

        rot = Rotation.from_euler('xyz', euler, degrees=True).as_rotvec()
        rot[2] *= -1
        rot = Rotation.from_euler('xyz', [0, 90.0, 0.0], degrees=degrees) * Rotation.from_rotvec(rot)
        return rot.as_matrix().T

    @classmethod
    def location_from_ue(cls, vector: np.ndarray) -> np.ndarray:
        """Convert from ue camera space to opencv camera space convention.

        [right, front, up]: (x, y, z) ==> (y, -z, x)

        Args:
            vector (np.ndarray): of shape (3,) or (... , 3)

        Returns:
            np.ndarray: of shape (3,) or (... , 3)
        """
        if isinstance(vector, list):
            vector = np.array(vector)
        if vector.shape == (3,):
            ret = np.array([vector[1], -vector[2], vector[0]]) / cls.units_scale
        elif vector.ndim >= 2 and vector.shape[-1] == 3:
            ret = np.stack([vector[..., 1], -vector[..., 2], vector[..., 0]], axis=-1) / cls.units_scale
        return ret


class ConverterBlender:
    R_BlenderView_to_OpenCVView = np.diag([1, -1, -1])

    @classmethod
    def rotation_from_blender(cls, euler, degrees=True) -> np.ndarray:
        """Convert from blender space to opencv camera space convention.

        Args:
            euler (np.ndarray): of shape (3,)
            degrees (bool, optional): Whether the input angles are in degrees. Defaults to True.

        Returns:
            np.ndarray: Rotation matrix 3x3.
        """
        euler = [-euler[0], euler[1], -euler[2]]
        mat = rotation_matrix(euler, order='xzy', degrees=degrees).T
        mat = cls.R_BlenderView_to_OpenCVView @ mat @ cls.R_BlenderView_to_OpenCVView.T
        return mat

    @classmethod
    def location_from_blender(cls, vector: np.ndarray) -> np.ndarray:
        """Convert from blender space to opencv camera space convention.

        [right, front, up]: (x, y, z) ==> (x, -z, y)

        Args:
            vector (np.ndarray): of shape (3,) or (... , 3)

        Returns:
            np.ndarray: of shape (3,) or (... , 3)
        """
        if isinstance(vector, (list, tuple)):
            vector = np.array(vector)
        if vector.shape == (3,):
            ret = np.array([vector[0], -vector[2], vector[1]])
        elif vector.ndim >= 2 and vector.shape[-1] == 3:
            ret = np.stack([vector[..., 0], -vector[..., 2], vector[..., 1]], axis=-1)
        return ret
