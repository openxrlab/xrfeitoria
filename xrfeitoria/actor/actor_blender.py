from pathlib import Path
from typing import Dict, Literal, Optional, Tuple

from loguru import logger

from ..data_structure.constants import Vector, default_level_blender
from ..object.object_utils import ObjectUtilsBlender
from ..rpc import remote_blender
from ..utils import Validator
from ..utils.functions import blender_functions
from .actor_base import ActorBase

try:
    import bpy  # isort:skip
    from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory  # defined in src/XRFeitoriaBpy/core/factory.py
except ModuleNotFoundError:
    pass

try:
    from ..data_structure.models import TransformKeys  # isort:skip
except ModuleNotFoundError:
    pass


@remote_blender(dec_class=True, suffix='_in_engine')
class ActorBlender(ActorBase):
    """Actor class for Blender."""

    _object_utils = ObjectUtilsBlender

    @property
    def dimensions(self) -> Vector:
        """Dimensions of the actor."""
        return self._object_utils.get_dimensions(self.name)

    @dimensions.setter
    def dimensions(self, value: 'Vector'):
        """Set dimensions of the actor.

        Args:
            value (Vector): Dimensions of the actor.
        """
        self._object_utils.set_dimensions(self.name, value)

    @property
    def bbox(self) -> 'Dict[Tuple[Vector, Vector]]':
        """Bounding box of the actor across all frames."""
        logger.info(f'[cyan]Getting bbox[/cyan] of "{self.name}" across all frames')
        logger.warning('This step is very time-consuming...')
        return self._object_utils.get_bbox(self.name)

    def set_origin_to_center(self) -> None:
        """Set origin of the object to its center."""
        self._object_utils.set_origin(self.name)

    def set_transform_keys(self, transform_keys: 'TransformKeys') -> None:
        """Set transform keys of actor.

        Args:
            transform_keys (List[Dict]): Keyframes of transform (frame, location, rotation, scale, and interpolation).
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        self._object_utils.set_transform_keys(name=self.name, transform_keys=transform_keys)

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _get_stencil_value_in_engine(actor_name: str) -> int:
        """Get stencil value (pass index) of the actor in Blender.

        Args:
            actor_name (str): Name of the actor.

        Returns:
            int: Stencil value (pass index).
        """
        return bpy.data.objects[actor_name].pass_index

    @staticmethod
    def _get_mask_color_in_engine(actor_name: str) -> 'Vector':
        """Get mask color of the actor in Blender.

        Args:
            actor_name (str): Name of the actor.

        Returns:
            Vector: Mask color. (r, g, b) in [0, 255].
        """
        pass_index = ActorBlender._get_stencil_value_in_engine(actor_name=actor_name)
        return (pass_index, pass_index, pass_index)

    @staticmethod
    def _set_stencil_value_in_engine(actor_name: str, value: int) -> int:
        """Set pass index (stencil value) of the actor in Blender.

        Args:
            actor_name (str): Name of the actor.
            value (int in [0, 255]): Pass index (stencil value).
        """
        object = bpy.data.objects[actor_name]
        object.pass_index = value
        for child in object.children:
            child.pass_index = value

    @staticmethod
    def _import_actor_from_file_in_engine(file_path: str, actor_name: str, collection_name: str = None) -> None:
        """Import actor from file.

        Args:
            path (str): File path used of the actor. Support: fbx | obj | alembic.
            name (str): Name of the actor in Blender.
            collection_name (str, optional): Name of the collection to import the actor to.
        Raises:
            TypeError: If 'path' is not `fbx | obj | alembic | ply | stl` file.
        """
        ## get scene and collection
        scene, collection = XRFeitoriaBlenderFactory.get_scene_and_collection_for_new_object(collection_name)

        # import
        with XRFeitoriaBlenderFactory.__judge__(name=actor_name, import_path=file_path, scene=scene):
            blender_functions.import_file(file_path=file_path)

    @staticmethod
    def _import_animation_from_file_in_engine(animation_path: str, actor_name: str, action_name: str = None) -> None:
        """Import an animation file.

        Args:
            animation_path (PathLike): File path used of the actor. Support: json | blend | fbx.
            name (str): Name of the actor to apply this animation.
            action_name (str, optional): Name of the action, only need when importing from a blend file.
                Defaults to None.

        Raises:
            TypeError: If 'animation_path' is not `json | blend | fbx` file.
        """
        anim_file_ext = Path(animation_path).suffix
        if anim_file_ext.lower() == '.json':
            XRFeitoriaBlenderFactory.import_mo_json(mo_json_file=animation_path, actor_name=actor_name)
        elif anim_file_ext.lower() == '.blend':
            XRFeitoriaBlenderFactory.import_mo_blend(
                mo_blend_file=animation_path, actor_name=actor_name, action_name=action_name
            )
        elif anim_file_ext.lower() == '.fbx':
            XRFeitoriaBlenderFactory.import_mo_fbx(mo_fbx_file=animation_path, actor_name=actor_name)
        else:
            raise TypeError(f"Invalid anim file, expected 'json', 'blend', or 'fbx' (got {anim_file_ext[1:]} instead).")


@remote_blender(dec_class=True, suffix='_in_engine')
class ShapeBlenderWrapper:
    """Wrapper class for shapes in Blender."""

    _object_utils = ObjectUtilsBlender

    @classmethod
    def spawn_cube(
        cls,
        name: str,
        size: float = 1.0,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
    ) -> 'ActorBlender':
        """Spawn a cube in the engine.

        Args:
            name (str): Name of the new added cube.
            size (float in [0, inf], optional): Size of the cube. Defaults to 1.0. (unit: meter)
            location (Vector, optional): Location of the cube. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the cube. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the cube. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the cube. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.


        Returns:
            ActorBlender: New added cube.
        """
        return cls.spawn(
            name=name,
            type='cube',
            location=location,
            rotation=rotation,
            scale=scale,
            stencil_value=stencil_value,
            size=size,
        )

    @classmethod
    def spawn_plane(
        cls,
        name: str,
        size: float = 1.0,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
    ) -> 'ActorBlender':
        """Spawn a plane in the engine.

        Args:
            name (str): Name of the new added plane.
            size (float in [0, inf], optional): Size of the plane. Defaults to 1.0. (unit: meter)
            location (Vector, optional): Location of the plane. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the plane. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the plane. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the plane. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ActorBlender: New added plane.
        """
        return cls.spawn(
            name=name,
            type='plane',
            location=location,
            rotation=rotation,
            scale=scale,
            stencil_value=stencil_value,
            size=size,
        )

    @classmethod
    def spawn_sphere(
        cls,
        name: str,
        radius: float = 1.0,
        segments: int = 32,
        ring_count: int = 16,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
    ) -> 'ActorBlender':
        """Spawn a `UV sphere <https://docs.blender.org/manual/en/latest/modeling/meshes/primitives.html#uv-sphere>`_ in the engine.

        Args:
            name (str): Name of the new added UV sphere.
            radius (float in [0, inf], optional): Radius of the UV sphere. Defaults to 1.0. (unit: meter)
            segments (int in [3, 100000], optional): Number of vertical segments on the sphere. Defaults to 32.
            ring_count (int in [3, 100000], optional): Number of horizontal segmentson the sphere. Defaults to 16.
            location (Vector, optional): Location of the UV sphere. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the UV sphere. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the UV sphere. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the UV sphere. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ActorBlender: New added UV sphere.
        """
        return cls.spawn(
            name=name,
            type='sphere',
            location=location,
            rotation=rotation,
            scale=scale,
            stencil_value=stencil_value,
            segments=segments,
            ring_count=ring_count,
            radius=radius,
        )

    @classmethod
    def spawn_ico_sphere(
        cls,
        name: str,
        radius: float = 1.0,
        subdivisions: int = 2,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
    ) -> 'ActorBlender':
        """Spawn an `icosphere <https://docs.blender.org/manual/en/latest/modeling/meshes/primitives.html#icosphere>`_ in the engine.

        Args:
            name (str): Name of the new added icosphere.
            radius (float in [0, inf], optional): Radius of the icosphere. Defaults to 1.0. (unit: meter)
            subdivisions (int in [1, 10], optional): Number of times of splitting each triangular face on the sphere into four triangles. Defaults to 2.
            location (Vector, optional): Location of the icosphere. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the icosphere. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the icosphere. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the icosphere. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ActorBlender: New added icosphere.
        """
        return cls.spawn(
            name=name,
            type='ico_sphere',
            location=location,
            rotation=rotation,
            scale=scale,
            stencil_value=stencil_value,
            subdivisions=subdivisions,
            radius=radius,
        )

    @classmethod
    def spawn_cylinder(
        cls,
        name: str,
        radius: float = 1.0,
        depth: float = 2.0,
        vertices: int = 32,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
    ) -> 'ActorBlender':
        """Spawn a cylinder in the engine.

        Args:
            name (str): Name of the new added cylinder.
            radius (float in [0, inf], optional): Radius of the cylinder's bases. Defaults to 1.0. (unit: meter)
            depth (float in [0, inf], optional): Height of the cylinder. Defaults to 2.0. (unit: meter)
            vertices (int in [3, 10000000], optional): Number of vertices on the circumference of the base of the cylinder. Defaults to 32.
            location (Vector, optional): Location of the cylinder. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the cylinder. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the cylinder. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the cylinder. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ActorBlender: New added cylinder.
        """
        return cls.spawn(
            name=name,
            type='cylinder',
            location=location,
            rotation=rotation,
            scale=scale,
            stencil_value=stencil_value,
            vertices=vertices,
            radius=radius,
            depth=depth,
        )

    @classmethod
    def spawn_cone(
        cls,
        name: str,
        radius1: float = 1.0,
        radius2: float = 0.0,
        depth: float = 2.0,
        vertices: int = 32,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
    ) -> 'ActorBlender':
        """Spawn a cone in the engine.

        Args:
            name (str): Name of the new added cone.
            radius1 (float in [0, inf], optional): Radius of the circular base of the cone. Defaults to 1.0. (unit: meter).
            radius2 (float in [0, inf], optional): Radius of the tip of the cone. Defaults to 0.0. (unit: meter).
            depth (float in [0, inf], optional): Height of the cone. Defaults to 2.0. (unit: meter)
            vertices (int in [3, 10000000], optional): Number of vertices on the circumference of the base of the cone. Defaults to 32.
            location (Vector, optional): Location of the cone. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the cone. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the cone. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the cone. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ActorBlender: New added cone.
        """
        return cls.spawn(
            name=name,
            type='cone',
            location=location,
            rotation=rotation,
            scale=scale,
            stencil_value=stencil_value,
            vertices=vertices,
            radius1=radius1,
            radius2=radius2,
            depth=depth,
        )

    @classmethod
    def spawn(
        cls,
        type: Literal['plane', 'cube', 'sphere', 'ico_sphere', 'cylinder', 'cone'],
        name: Optional[str] = None,
        location: Vector = (0, 0, 0),
        rotation: Vector = (0, 0, 0),
        scale: Vector = (1, 1, 1),
        stencil_value: int = 1,
        **kwargs,
    ) -> 'ActorBlender':
        """Spawn a shape(plane, cube, UV sphere, icosphere, cylinder or cone) in the
        scene.

        Args:
            name (str): Name of the new added shape.
            mesh_type (enum in ['plane', 'cube', 'sphere', 'icosphere', 'cylinder', 'cone']): Type of new spawn shape.
            location (Vector, optional): Location of the shape. Defaults to (0, 0, 0).
            rotation (Vector, optional): Rotation of the shape. Defaults to (0, 0, 0).
            scale (Vector, optional): Scale of the shape. Defaults to (1, 1, 1).
            stencil_value (int in [0, 255], optional): Stencil value of the shape. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.
            **kwargs
                - ``plane``: size. Ref to :meth:`ShapeBlenderWrapper.spawn_plane <xrfeitoria.actor.actor_blender.ShapeBlenderWrapper.spawn_plane>` for details.
                - ``cube``: size. Ref to :meth:`ShapeBlenderWrapper.spawn_cube <xrfeitoria.actor.actor_blender.ShapeBlenderWrapper.spawn_cube>` for details.
                - ``sphere``: radius, segments, ring_count. Ref to :meth:`ShapeBlenderWrapper.spawn_sphere <xrfeitoria.actor.actor_blender.ShapeBlenderWrapper.spawn_sphere>` for details.
                - ``icosphere``: radius, subdivisions. Ref to :meth:`ShapeBlenderWrapper.spawn_ico_sphere <xrfeitoria.actor.actor_blender.ShapeBlenderWrapper.spawn_ico_sphere>` for details.
                - ``cylinder``: radius, depth, vertices. Ref to :meth:`ShapeBlenderWrapper.spawn_cylinder <xrfeitoria.actor.actor_blender.ShapeBlenderWrapper.spawn_cylinder>` for details.
                - ``cone``: radius1, radius2, depth, vertices. Ref to :meth:`ShapeBlenderWrapper.spawn_cone <xrfeitoria.actor.actor_blender.ShapeBlenderWrapper.spawn_cone>` for details.
        Returns:
            ActorBlender: New added shape.
        """
        if name is None:
            name = cls._object_utils.generate_obj_name(obj_type=type)
        cls._object_utils.validate_new_name(name)
        Validator.validate_vector(location, 3)
        Validator.validate_vector(rotation, 3)
        Validator.validate_vector(scale, 3)

        cls._object_utils.validate_new_name(name)
        cls._spawn_shape_in_engine(
            name=name,
            type=type,
            **kwargs,
        )
        mesh = ActorBlender(name=name)
        mesh.set_transform(location, rotation, scale)
        mesh.stencil_value = stencil_value
        logger.info(f'[cyan]Spawned[/cyan] {type} "{name}"')
        return mesh

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _spawn_shape_in_engine(
        name: str,
        type: str,
        collection_name: str = None,
        size: float = 1.0,
        segments: int = 32,
        ring_count: int = 16,
        radius: float = 1.0,
        subdivisions: int = 2,
        vertices: int = 32,
        depth: float = 2.0,
        radius1: float = 0.0,
        radius2: float = 2.0,
    ) -> None:
        """Spawn a shape in Blender.

        Args:
            name (str): Name of the new added shape.
            mesh_type (enum in ['plane', 'cube', 'UV sphere', 'icosphere', 'cylinder', 'cone']): Type of new spawn shape.
            size (float in [0, inf], optional): Size. Defaults to 1.0. (unit: meter)
            segments (int in [3, 100000], optional): Segments. Defaults to 32.
            ring_count (int in [3, 100000], optional): Ring count. Defaults to 16.
            radius (float in [0, inf], optional): Radius. Defaults to 1.0. (unit: meter)
            subdivisions (int in [1, 10], optional): Subdivisions. Defaults to 2.
            vertices (int in [3, 10000000], optional): Vertices. Defaults to 32.
            depth (float in [0, inf], optional): Depth. Defaults to 2.0. (unit: meter)
            radius1 (float in [0, inf], optional): Radius1. Defaults to 0.0. (unit: meter)
            radius2 (float in [0, inf], optional): Radius2. Defaults to 2.0. (unit: meter)

        Raises:
            TypeError: If `mesh_type` is not in Enum ['plane', 'cube', 'UV sphere', 'icosphere', 'cylinder', 'cone']
        """

        ## get scene and collection
        scene, collection = XRFeitoriaBlenderFactory.get_scene_and_collection_for_new_object(collection_name)

        # spawn mesh
        with XRFeitoriaBlenderFactory.__judge__(name, scene=scene):
            if type == 'plane':
                bpy.ops.mesh.primitive_plane_add(size=size)
            elif type == 'cube':
                bpy.ops.mesh.primitive_cube_add(size=size)
            elif type == 'sphere':
                bpy.ops.mesh.primitive_uv_sphere_add(
                    segments=segments,
                    ring_count=ring_count,
                    radius=radius,
                )
            elif type == 'ico_sphere':
                bpy.ops.mesh.primitive_ico_sphere_add(
                    subdivisions=subdivisions,
                    radius=radius,
                )
            elif type == 'cylinder':
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=vertices,
                    radius=radius,
                    depth=depth,
                )
            elif type == 'cone':
                bpy.ops.mesh.primitive_cone_add(
                    vertices=vertices,
                    radius1=radius1,
                    radius2=radius2,
                    depth=depth,
                )
            else:
                raise TypeError(
                    f'Unsupported mesh type, expected "plane", "cube", "sphere", '
                    f'"ico_sphere", "cylinder" or "cone", (got "{type}" instead).'
                )
