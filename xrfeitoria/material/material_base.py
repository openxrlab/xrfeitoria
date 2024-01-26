from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..data_structure.constants import PathLike
from ..object.object_utils import ObjectUtilsBase


class MaterialBase(ABC):
    """Base material class."""

    _object_utils = ObjectUtilsBase

    def __init__(self, name: str) -> None:
        """
        Args:
            name (str): name of the object
        """
        self._name = name

    @classmethod
    def new(cls, mat_name: str) -> 'MaterialBase':
        """Add a new material.

        Args:
            mat_name (str): Name of the material.

        Returns:
            MaterialBase: Material object.
        """
        cls._new_material_in_engine(mat_name)
        return cls(mat_name)

    def add_diffuse_texture(
        self,
        texture_file: PathLike,
        texture_name: Optional[str] = None,
    ) -> None:
        """Add a diffuse texture to the material.

        Args:
            texture_file (PathLike): File path of the texture.
            texture_name (Optional[str]): Name of the texture. Defaults to None.
        """
        if texture_name is None:
            texture_name = Path(texture_file).stem
        self._add_diffuse_texture_in_engine(mat_name=self._name, texture_file=texture_file, texture_name=texture_name)

    def add_normal_texture(
        self,
        texture_file: PathLike,
        texture_name: Optional[str] = None,
    ) -> None:
        """Add a normal texture to the material.

        Args:
            texture_file (PathLike): File path of the texture.
            texture_name (Optional[str]): Name of the texture. Defaults to None.
        """
        if texture_name is None:
            texture_name = Path(texture_file).stem
        self._add_normal_texture_in_engine(mat_name=self._name, texture_file=texture_file, texture_name=texture_name)

    def add_roughness_texture(
        self,
        texture_file: PathLike,
        texture_name: Optional[str] = None,
    ) -> None:
        """Add a roughness texture to the material.

        Args:
            texture_file (PathLike): File path of the texture.
            texture_name (Optional[str]): Name of the texture. Defaults to None.
        """
        if texture_name is None:
            texture_name = Path(texture_file).stem
        self._add_roughness_texture_in_engine(mat_name=self._name, texture_file=texture_file, texture_name=texture_name)

    #################################
    ####  RPC METHODS (Private)  ####
    #################################

    @staticmethod
    @abstractmethod
    def _new_material_in_engine(mat_name: str) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _add_diffuse_texture_in_engine(
        mat_name: str,
        texture_file: str,
        texture_name: str,
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _add_normal_texture_in_engine(
        mat_name: str,
        texture_file: str,
        texture_name: str,
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def _add_roughness_texture_in_engine(
        mat_name: str,
        texture_file: str,
        texture_name: str,
    ) -> None:
        pass
