import copy
import math
from typing import List, Tuple, Union

import numpy as np
import numpy.typing as npt
from loguru import logger
from xrprimer.data_structure.camera import PinholeCameraParameter
from xrprimer.transform.convention.camera import convert_camera_parameter

from ..data_structure.constants import PathLike, Vector


class CameraParameter(PinholeCameraParameter):
    """Camera parameter class for pinhole camera model.

    Inherit from XRPrimer.
    """

    def __init__(
        self,
        K: Union[List, np.ndarray],
        R: Union[List, np.ndarray],
        T: Union[List, np.ndarray],
        convention: str = 'opencv',
        world2cam: bool = False,
    ):
        """A camera parameter class for pinhole camera model.

        Args:
            K (Union[list, np.ndarray]):
                Nested list of float32, 4x4 or 3x3 K mat.
            R (Union[list, np.ndarray]):
                Nested list of float32, 3x3 rotation mat.
            T (Union[list, np.ndarray, None]):
                List of float32, T vector.
            convention (str, optional):
                Convention name of this camera.
                Defaults to 'opencv'.
            world2cam (bool, optional):
                Whether the R, T transform points from world space
                to camera space. Defaults to True.
        """
        width, height = int(K[0][2] * 2), int(K[1][2] * 2)
        super().__init__(
            K,
            R,
            T,
            width=width,
            height=height,
            convention=convention,
            world2cam=world2cam,
            logger=logger,
        )
        # type hinting
        self.intrinsic: npt.NDArray[np.float32]  # 4x4
        self.extrinsic_r: npt.NDArray[np.float32]  # 3x3
        self.extrinsic_t: npt.NDArray[np.float32]  # 3
        self.height: int
        self.width: int
        self.convention: str
        self.world2cam: bool

    def clone(self) -> 'CameraParameter':
        """Clone a new CameraParameter instance like self.

        Returns:
            CameraParameter
        """
        new_cam_param = self.__class__(
            K=copy.deepcopy(self.get_intrinsic(k_dim=4)),
            R=copy.deepcopy(self.extrinsic_r),
            T=copy.deepcopy(self.extrinsic_t),
            world2cam=self.world2cam,
            convention=self.convention,
        )
        return new_cam_param

    @property
    def projection_matrix(self) -> npt.NDArray[np.float32]:
        """Get the camera matrix of ``K@RT``.

        Returns:
            ndarray: An ndarray of float32, 3x4 ``K@RT`` mat.
        """
        return self.intrinsic33() @ self.extrinsic

    @property
    def extrinsic(self) -> npt.NDArray[np.float32]:
        """Get the extrinsic matrix of RT.

        Returns:
            ndarray: An ndarray of float32, 3x4 RT mat.
        """
        return np.concatenate([self.extrinsic_r, self.extrinsic_t.reshape(3, 1)], axis=1)

    def get_projection_matrix(self) -> List:
        """Get the camera matrix of ``K@RT``.

        Returns:
            List: A list of float32, 3x4 ``K@RT`` mat.
        """
        return self.projection_matrix.tolist()

    def get_extrinsic(self) -> List:
        """Get the camera matrix of RT.

        Returns:
            List: A list of float32, 3x4 RT mat.
        """
        return self.extrinsic.tolist()

    def model_dump(self) -> dict:
        """Dump camera parameters to a dict."""
        return {
            'class_name': 'PinholeCameraParameter',
            'convention': self.convention,
            'extrinsic_r': self.extrinsic_r.tolist(),
            'extrinsic_t': self.extrinsic_t.tolist(),
            'height': self.height,
            'width': self.width,
            'intrinsic': self.intrinsic.tolist(),
            'name': self.name,
            'world2cam': self.world2cam,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CameraParameter':
        """Construct a camera parameter data structure from a dict.

        Args:
            data (dict): The camera parameter data.

        Returns:
            CameraParameter: An instance of CameraParameter class.
        """
        return cls(
            K=data['intrinsic'],
            R=data['extrinsic_r'],
            T=data['extrinsic_t'],
            convention=data['convention'],
            world2cam=data['world2cam'],
        )

    @classmethod
    def fromfile(cls, file: PathLike) -> 'CameraParameter':
        """Construct a camera parameter data structure from a json file.

        Args:
            filename (PathLike): Path to the dumped json file.

        Returns:
            CameraParameter: An instance of CameraParameter class.
        """
        file = str(file)
        ret_cam = PinholeCameraParameter.fromfile(file)
        return cls._from_pinhole(ret_cam)

    @classmethod
    def from_bin(cls, file: PathLike) -> 'CameraParameter':
        """Construct a camera parameter data structure from a binary file.

        Args:
            file (PathLike): Path to the dumped binary file.

        Returns:
            CameraParameter: An instance of CameraParameter class.
        """
        # read camera parameters
        with open(file, 'rb') as f:
            dat = np.frombuffer(f.read(), np.float32).reshape(9)
        location = dat[:3]
        rotation = dat[3:6]
        camera_fov = dat[6]
        image_size = (dat[7], dat[8])  # (width, height)
        return cls.from_unreal_convention(location, rotation, camera_fov, image_size)

    @classmethod
    def from_unreal_convention(
        cls,
        location: Vector,
        rotation: Vector,
        fov: float,
        image_size: Tuple[int, int],  # (width, height)
    ) -> 'CameraParameter':
        """Converts camera parameters from Unreal Engine convention to CameraParameter
        object.

        Args:
            location (Vector): The camera location in Unreal Engine convention.
            rotation (Vector): The camera rotation in Unreal Engine convention.
            fov (float): The camera field of view in degrees.
            image_size (Tuple[int, int]): The size of the camera image in pixels (width, height).

        Returns:
            CameraParameter: The converted camera parameters.
        """
        # intrinsic matrix K
        fov = math.radians(fov)
        focal = max(image_size) / 2 / math.tan(fov / 2)
        fx = fy = focal
        K = np.array(
            [
                [fx, 0, image_size[0] / 2],
                [0, fy, image_size[1] / 2],
                [0, 0, 1],
            ]
        )

        # extrinsic matrix RT
        x, y, z = -rotation[1], -rotation[2], -rotation[0]
        R = rotation_matrix([x, y, z], order='xyz', degrees=True)
        _T = np.array([location[1], -location[2], location[0]]) / 100.0  # unit: meter
        T = -R @ _T

        # construct camera parameter
        cam_param = cls(K=K, R=R, T=T, world2cam=True)
        return cam_param

    @classmethod
    def _from_pinhole(cls, pinhole: PinholeCameraParameter) -> 'CameraParameter':
        """Construct a camera parameter data structure from a pinhole camera parameter.

        Args:
            pinhole (PinholeCameraParameter):
                An instance of PinholeCameraParameter class.

        Returns:
            CameraParameter:
                An instance of CameraParameter class.
        """
        ret_cam = cls(
            K=pinhole.get_intrinsic(k_dim=4),
            R=pinhole.extrinsic_r,
            T=pinhole.extrinsic_t,
            convention=pinhole.convention,
            world2cam=pinhole.world2cam,
        )
        return ret_cam

    def convert_convention(self, dst: str):
        """Convert the convention of this camera parameter. In-place.

        Args:
            dst (str): The name of destination convention. One of ['opencv', 'blender', 'unreal'].
        """
        cam_param = convert_camera_parameter(self, dst)
        self.set_KRT(K=cam_param.intrinsic, R=cam_param.extrinsic_r, T=cam_param.extrinsic_t)
        self.convention = dst
        self.world2cam = cam_param.world2cam

    def __repr__(self) -> str:
        return f'CameraParameter(T={self.extrinsic_t}, convention="{self.convention}", world2cam={self.world2cam})'


def rotation_matrix(angles: Tuple[float, float, float], order='xyz', degrees: bool = True) -> npt.NDArray[np.float32]:
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
