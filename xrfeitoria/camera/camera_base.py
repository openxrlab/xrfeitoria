from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple

from loguru import logger

from ..data_structure.constants import Matrix, PathLike, Vector
from ..object.object_base import ObjectBase
from ..object.object_utils import ObjectUtilsBase
from ..utils import Validator


class CameraBase(ABC, ObjectBase):
    """Base camera class."""

    _object_utils = ObjectUtilsBase

    @classmethod
    def spawn(
        cls,
        camera_name: str = None,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        fov: float = 90.0,
    ) -> 'CameraBase':
        """Spawn a camera in the engine.

        Args:
            name (str, optional): name of the camera
            location (Vector, optional): location of the camera. Defaults to (0, 0, 0).
            rotation (Vector, optional): rotation of the camera. Defaults to (0, 0, 0).
            fov (float, optional): field of view of the camera. Defaults to 90.0.
        Returns:
            CameraBase: New camera
        """
        if camera_name is None:
            camera_name = cls._object_utils.generate_obj_name(obj_type='camera')
        cls._object_utils.validate_new_name(camera_name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_argument_type(fov, [float, int])
        cls._spawn_in_engine(camera_name=camera_name, location=location, rotation=rotation, fov=fov)
        logger.info(f'[cyan]Spawned[/cyan] camera "{camera_name}"')
        return cls(camera_name)

    @property
    def fov(self) -> float:
        """Field of view of the camera lens, in degrees."""
        return self._get_fov_in_engine(self._name)

    @fov.setter
    def fov(self, value):
        Validator.validate_argument_type(value, [float, int])
        self._set_camera_fov_in_engine(self._name, value)

    def get_KRT(self) -> Tuple[List, List, Vector]:
        """Get the intrinsic and extrinsic parameters of the camera.

        Returns:
            Tuple[Matrix, Matrix, Vector]: K, R, T
        """
        return self._get_KRT_in_engine(self._name)

    def set_KRT(self, K: List, R: List, T: Vector) -> None:
        """Set the intrinsic and extrinsic parameters of the camera.

        Args:
            K (Matrix): 3x3 intrinsic matrix
            R (Matrix): 3x3 rotation matrix
            T (Vector): 3x1 translation vector
        """
        self._set_KRT_in_engine(self._name, K, R, T)

    def dump_params(self, output_path: PathLike) -> None:
        """Dump the intrinsic and extrinsic parameters of the camera to a file.

        Args:
            output_path (PathLike): path to the camera parameter file
        """
        from .camera_parameter import CameraParameter

        # mkdir
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # dump
        K, R, T = self.get_KRT()
        camera_param = CameraParameter(K=K, R=R, T=T)
        camera_param.dump(output_path.as_posix())
        logger.debug(f'Camera parameters dumped to "{output_path.as_posix()}"')

    def look_at(self, target: Vector) -> None:
        """Set the camera to look at the target.

        Args:
            target (Vector): [x, y, z] coordinates of the target, in units of meters.
        """
        # TODO: get rid of _look_at_in_engine, calculate the rotation matrix from the direction vector
        # direction = np.array(target) - np.array(self.location)
        # self.rotation = self._object_utils.direction_to_euler(direction)
        self._look_at_in_engine(self._name, target)

    #################################
    ####  RPC METHODS (Private)  ####
    #################################

    # ----- Getter ----- #

    @staticmethod
    @abstractmethod
    def _get_KRT_in_engine(name: str):
        pass

    @staticmethod
    @abstractmethod
    def _get_fov_in_engine(name: str) -> float:
        pass

    # ----- Setter ----- #

    @staticmethod
    @abstractmethod
    def _set_KRT_in_engine(name, K, R, T):
        pass

    @staticmethod
    @abstractmethod
    def _set_camera_fov_in_engine(name: str, value: float):
        pass

    @staticmethod
    @abstractmethod
    def _spawn_in_engine(camera_name, location, rotation, fov):
        pass

    @staticmethod
    @abstractmethod
    def _look_at_in_engine(name, target):
        pass
