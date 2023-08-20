from ..constants import Transform, Vector
from .object_utils import ObjectUtilsBase


class ObjectBase:
    _object_utils = ObjectUtilsBase

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        self._object_utils.set_name(self._name, value)

    @property
    def location(self) -> Vector:
        """
        Location of the object in the world, in meters

        Returns:
            Tuple[float, float, float]: in meters
        """
        return self._object_utils.get_location(self._name)

    @location.setter
    def location(self, value: Vector):
        self._location = value
        self._object_utils.set_location(self._name, self._location)

    @property
    def rotation(self) -> Vector:
        """
        Rotation of the object in the world, in degrees

        Returns:
            Tuple[float, float, float]: in degrees
        """
        return self._object_utils.get_rotation(self._name)

    @rotation.setter
    def rotation(self, value: Vector):
        self._rotation = value
        self._object_utils.set_rotation(self._name, self._rotation)

    @property
    def scale(self) -> Vector:
        """
        Scale of the object in the world, no units

        Returns:
            Tuple[float, float, float]: no units, 1.0 is default
        """
        return self._object_utils.get_scale(self._name)

    @scale.setter
    def scale(self, value: Vector):
        self._scale = value
        self._object_utils.set_scale(self._name, self._scale)

    def get_transform(self) -> Transform:
        """Get the transform of the object in the world"""
        return self._object_utils.get_transform(self._name)

    def set_transform(self, location: Vector, rotation: Vector, scale: Vector):
        self._object_utils.set_transform(self._name, location, rotation, scale)

    def delete(self):
        self._object_utils.delete_obj(self._name)
        del self

    def rename(self, new_name: str):
        self._object_utils.set_name(self._name, new_name)
        self._name = new_name

    # @classmethod
    # def delete_by_name(cls, name):
    #     cls._engine_functions.delete_obj(name)

    # @classmethod
    # def rename_by_name(cls, name, new_name):
    #     cls._engine_functions.set_name(name, new_name)

    # @classmethod
    # def delete_all(cls):
    #     cls._engine_functions.delete_all()
