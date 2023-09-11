from typing import List, Tuple

from loguru import logger

from ..data_structure.constants import Vector
from .object_utils import ObjectUtilsBase


class ObjectBase:
    """Base class for all objects in the world."""

    _object_utils = ObjectUtilsBase

    def __init__(self, name: str) -> None:
        """
        Args:
            name (str): name of the object
        """
        self._name = name

    @property
    def name(self) -> str:
        """Name of the object."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set new name of the object.

        Args:
            value (str): New name of the object.
        """
        self._object_utils.set_name(self.name, value)
        self._name = value

    @property
    def location(self) -> Vector:
        """Location of the object in the world, in meters."""
        return self._object_utils.get_location(self._name)

    @location.setter
    def location(self, value: Vector):
        """Set location of the object.

        Args:
            value (Vector): Location of object. (unit: meter)
        """
        self._object_utils.set_location(self._name, value)

    @property
    def rotation(self) -> Vector:
        """Rotation of the object in the world, in degrees."""
        return self._object_utils.get_rotation(self._name)

    @rotation.setter
    def rotation(self, value: Vector):
        """Set rotation of the object.

        Args:
            value (Vector): Rotation of the object. (unit: degrees)
        """
        self._object_utils.set_rotation(self._name, value)

    @property
    def scale(self) -> Vector:
        """Scale of the object in the world, no units, 1.0 is default."""
        return self._object_utils.get_scale(self._name)

    @scale.setter
    def scale(self, value: Vector):
        """Set scale of the object.

        Args:
            value (Vector): Scale of the object.
        """
        self._object_utils.set_scale(self._name, value)

    def get_transform(self) -> Tuple[List, List, List]:
        """Get the transform of the object in the world.

        Returns:
            Transform: location, rotation, scale
        """
        return self._object_utils.get_transform(self._name)

    def set_transform(self, location: Vector, rotation: Vector, scale: Vector) -> None:
        """Set the transform of the object in the world.

        Args:
            location (Tuple[float, float, float]): in meters
            rotation (Tuple[float, float, float]): in degrees
            scale (Tuple[float, float, float]): no units, 1.0 is default
        """
        self._object_utils.set_transform(self._name, location, rotation, scale)

    def delete(self):
        """Delete the object from the world."""
        self._object_utils.delete_obj(self._name)
        logger.info(f'[red]Deleted[/red] object "{self.name}"')
        del self
