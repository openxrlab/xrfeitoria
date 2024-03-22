"""Converter for different spaces."""

from typing import Literal, Union

import numpy as np

from ..data_structure.constants import Vector


def euler_to_rot_matrix(angles: Union[Vector, np.ndarray], order='xyz', degrees: bool = True) -> np.ndarray:
    """Convert Euler angles to rotation matrix.

    This function is to avoid importing third-party libraries like `transforms3d` or `scipy`, for saving the size of the package.

    Args:
        angles (Tuple[float, float, float]): Rotation angles in degrees or radians.
        order (str, optional): Rotation order. Defaults to 'xyz'.
        degrees (bool, optional): Whether the input angles are in degrees. Defaults to True.
    Returns:
        ndarray: Rotation matrix 3x3.

    Examples:
        >>> euler_to_to_matrix((0, 0, 0), order='xyz')
        array([[ 1.,  0.,  0.],
               [ 0.,  1.,  0.],
               [ 0.,  0.,  1.]])

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


def quat_to_rot_matrix(quat, order: Literal['xyzw', 'wxyz'] = 'xyzw') -> np.ndarray:
    """Convert a quaternion to a rotation matrix.

    This function is to avoid importing third-party libraries like `transforms3d` or `scipy`, for saving the size of the package.

    Args:
        quat: A list or array-like object representing the quaternion in the order specified by the `order` parameter.
        order: The order of the quaternion elements. Must be either 'xyzw' or 'wxyz'. Defaults to 'xyzw'.

    Returns:
        A 3x3 numpy array representing the rotation matrix.

    Raises:
        ValueError: If the `order` parameter is not 'xyzw' or 'wxyz'.

    Examples:
        >>> quat_to_rot_matrix([0.707, 0.0, 0.0, 0.707])
        array([[ 1.,  0.,  0.],
               [ 0., -1.,  0.],
               [ 0.,  0., -1.]])
    """
    if order == 'xyzw':
        x, y, z, w = quat
    elif order == 'wxyz':
        w, x, y, z = quat
    else:
        raise ValueError(f'Unknown order: {order}')

    r11 = 1 - 2 * (y**2 + z**2)
    r12 = 2 * (x * y - z * w)
    r13 = 2 * (x * z + y * w)
    r21 = 2 * (x * y + z * w)
    r22 = 1 - 2 * (x**2 + z**2)
    r23 = 2 * (y * z - x * w)
    r31 = 2 * (x * z - y * w)
    r32 = 2 * (y * z + x * w)
    r33 = 1 - 2 * (x**2 + y**2)

    return np.array([[r11, r12, r13], [r21, r22, r23], [r31, r32, r33]])


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
        if isinstance(vector, (list, tuple)):
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
        if isinstance(vector, (list, tuple)):
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
    unreal2opencv = np.array(
        [
            [0, 1, 0],
            [0, 0, -1],
            [1, 0, 0],
        ]
    )

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
        return euler_to_rot_matrix([x, y, z], order='xyz', degrees=degrees)

    @classmethod
    def quat_from_ue(cls, quat) -> np.ndarray:
        """Convert from ue camera space to opencv camera space convention.

        Args:
            euler (np.ndarray): of shape (3,)
            offset (np.ndarray, optional): of shape (3,). Defaults to ROTATION_OFFSET [0, 0, -90.0].
            degrees (bool, optional): Whether the input angles are in degrees. Defaults to True.

        Returns:
            np.ndarray: Rotation matrix 3x3.
        """

        rot_unreal = quat_to_rot_matrix(quat, order='xyzw').T
        rot_unreal = cls.unreal2opencv @ rot_unreal @ cls.unreal2opencv.T
        rot = euler_to_rot_matrix([0, 90.0, 0.0], 'xyz', degrees=True) @ rot_unreal
        return rot.T

    @classmethod
    def location_from_ue(cls, vector: np.ndarray) -> np.ndarray:
        """Convert from ue camera space to opencv camera space convention.

        [right, front, up]: (x, y, z) ==> (y, -z, x)

        Args:
            vector (np.ndarray): of shape (... , 3)

        Returns:
            np.ndarray: of shape (... , 3)
        """
        return np.einsum('ij,...j->...i', cls.unreal2opencv, vector) / cls.units_scale


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
        mat = euler_to_rot_matrix(euler, order='xzy', degrees=degrees).T
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
