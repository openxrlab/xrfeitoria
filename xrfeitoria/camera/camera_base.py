from abc import ABC, abstractmethod

from ..constants import Vector
from ..object import ObjectBase, ObjectUtilsBlender
from ..utils import Validator


class CameraBase(ABC, ObjectBase):
    _object_utils = ObjectUtilsBlender

    @classmethod
    def spawn_camera(
        cls,
        name: str,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        fov: float = 90.0,
    ) -> "CameraBase":
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_argument_type(fov, [float, int])
        cls._setup_camera_in_engine(name, location, rotation, fov)
        return cls(name)

    @property
    def fov(self) -> float:
        return self._get_camera_fov_in_engine(self._name)

    @fov.setter
    def fov(self, value):
        Validator.validate_argument_type(value, [float, int])
        self._set_camera_fov_in_engine(self._name, value)

    @property
    def active(self) -> bool:
        return self._get_camera_active_in_engine(self._name)

    @active.setter
    def active(self, value):
        Validator.validate_argument_type(value, bool)
        self._set_camera_active_in_engine(self._name, value)

    def get_KRT(self) -> tuple:
        return self._get_camera_KRT_in_engine(self._name)

    def set_KRT(self, K, R, T):
        self._set_camera_KRT_in_engine(self._name, K, R, T)

    #################################
    ####  RPC METHODS (Private)  ####
    #################################

    ######   Getter   ######

    @staticmethod
    @abstractmethod
    def _get_camera_KRT_in_engine(name):
        pass

    @staticmethod
    @abstractmethod
    def _get_camera_fov_in_engine(name) -> float:
        pass

    ######   Setter   ######
    @staticmethod
    @abstractmethod
    def _setup_camera_in_engine(name, location, rotation, fov):
        pass

    @staticmethod
    @abstractmethod
    def _get_camera_fov_in_engine(name) -> float:
        pass

    # ----- Setter ----- #

    @staticmethod
    @abstractmethod
    def _setup_camera_in_engine(name, location, rotation, fov):
        pass
