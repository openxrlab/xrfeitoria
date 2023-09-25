from typing import Dict, List, Optional, Tuple, Union

from ..actor.actor_blender import ActorBlender, ShapeBlenderWrapper
from ..camera.camera_blender import CameraBlender
from ..data_structure.constants import PathLike, Vector
from ..object.object_utils import ObjectUtilsBlender
from ..renderer.renderer_blender import RendererBlender
from ..rpc import remote_blender
from .sequence_base import SequenceBase

try:
    import bpy  # isort:skip
    from ..data_structure.models import TransformKeys  # isort:skip
    from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory  # defined in src/XRFeitoriaBpy/core/factory.py
except ModuleNotFoundError:
    pass


@remote_blender(dec_class=True, suffix='_in_engine')
class SequenceBlender(SequenceBase):
    """Sequence class for Blender."""

    _actor = ActorBlender
    _camera = CameraBlender
    _renderer = RendererBlender
    _object_utils = ObjectUtilsBlender

    # -------- spawn methods -------- #

    @classmethod
    def import_actor_with_keys(
        cls,
        file_path: PathLike,
        transform_keys: 'TransformKeys',
        actor_name: str = None,
        stencil_value: int = 1,
    ) -> 'ActorBlender':
        """Import an actor from a file to the sequence and add transform keyframes to
        the it.

        Args:
            name (str): Name of the actor in Blender.
            path (PathLike): File path used for importing the actor.
            transform_keys (TransformKeys):Keyframes of transform (location, rotation, and scale).
            stencil_value (int in [0, 255], optional): Stencil value of the actor. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.

        Returns:
            ActorBlender: New imported actor.
        """
        actor = cls.import_actor(
            actor_name=actor_name,
            file_path=file_path,
            stencil_value=stencil_value,
        )
        cls._object_utils.set_transform_keys(name=actor.name, transform_keys=transform_keys)
        return actor

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _new_seq_in_engine(
        level: str = None,
        seq_name: str = 'Sequence',
        seq_fps: int = 60,
        seq_length: int = 1,
        replace: bool = False,
    ) -> None:
        """Create a new sequence in Blender. (Create a collection named 'seq_name' and
        link it to the scene named 'level').

        Args:
            seq_name (str): _description_
            link_levels (Optional[Union[List[str],str]], optional): _description_. Defaults to [].
            seq_fps (Optional[float], optional): _description_. Defaults to None.
            seq_length (Optional[int], optional): _description_. Defaults to None.
            replace (bool, optional): _description_. Defaults to False.
        """
        # get level scene
        level_scene = (
            XRFeitoriaBlenderFactory.get_scene(level) if level else XRFeitoriaBlenderFactory.get_active_scene()
        )
        # new collection named seq_name
        new_seq_collection = XRFeitoriaBlenderFactory.new_collection(name=seq_name, replace=replace)
        # link sequence(new_seq_collection) to level(level_scene)
        XRFeitoriaBlenderFactory.link_collection_to_scene(collection=new_seq_collection, scene=level_scene)
        XRFeitoriaBlenderFactory.set_level_properties(scene=level_scene, active_seq=new_seq_collection)

        # set sequence properties
        XRFeitoriaBlenderFactory.set_sequence_properties(
            collection=new_seq_collection,
            level=level_scene,
            fps=seq_fps,
            frame_start=0,
            frame_end=seq_length - 1,
            frame_current=0,
        )
        level_scene.frame_start = 0
        level_scene.frame_end = seq_length - 1
        level_scene.frame_current = 0
        level_scene.render.fps = seq_fps
        # set scene to active
        XRFeitoriaBlenderFactory.set_scene_active(level_scene)
        # set collection to active
        XRFeitoriaBlenderFactory.set_collection_active(new_seq_collection)
        # tag the collection as sequence collection
        XRFeitoriaBlenderFactory.tag_sequence_collection(collection=new_seq_collection)

    @staticmethod
    def _open_seq_in_engine(seq_name: str) -> None:
        """Open an exist sequence in Blender. (Link the collection of the sequence to
        its level scene.)

        Args:
            seq_name (str): Name of the sequence.
        """
        # XRFeitoriaBlenderFactory.open_sequence(seq_name)
        level_scene = XRFeitoriaBlenderFactory.get_active_scene()
        active_sequence = XRFeitoriaBlenderFactory.get_collection(seq_name)
        XRFeitoriaBlenderFactory.set_level_properties(scene=level_scene, active_seq=active_sequence)

    @staticmethod
    def _close_seq_in_engine() -> None:
        """Close the opened sequence in Blender.

        (Unlink the collection of the sequence from the active scene.)
        """
        # XRFeitoriaBlenderFactory.close_sequence()
        level_scene = XRFeitoriaBlenderFactory.get_active_scene()
        XRFeitoriaBlenderFactory.set_level_properties(scene=level_scene, active_seq=None)

    @staticmethod
    def _show_seq_in_engine() -> None:
        raise NotImplementedError

    # -------- spawn methods -------- #
    @staticmethod
    def _import_actor_in_engine(
        file_path: str,
        transform_keys: 'Union[List[Dict], Dict]',
        actor_name: str = 'Actor',
        stencil_value: int = 1,
    ) -> None:
        """Import

        Args:
            file_path (PathLike): _description_
            transform_keys (Union[List[Dict], Dict]): _description_
            actor_name (str, optional): _description_. Defaults to 'Actor'.
            stencil_value (int, optional): _description_. Defaults to 1.
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]

        ActorBlender._import_actor_from_file_in_engine(file_path=file_path, actor_name=actor_name)
        ObjectUtilsBlender._set_transform_keys_in_engine(obj_name=actor_name, transform_keys=transform_keys)
        # XXX: set stencil value. may use actor property
        bpy.data.objects[actor_name].pass_index = stencil_value

    @staticmethod
    def _spawn_camera_in_engine(
        transform_keys: 'Union[List[Dict], Dict]',
        fov: float = 90.0,
        camera_name: str = 'Camera',
    ) -> None:
        """Spawn a camera in the engine.

        Args:
            transform_keys (Union[List[Dict], Dict]): Keyframes of transform (location, rotation, and scale).
            fov (float, optional): Field of view of the camera lens, in degrees. Defaults to 90.0.
            camera_name (str, optional): Name of the camera. Defaults to 'Camera'.
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]

        CameraBlender._spawn_in_engine(camera_name=camera_name, fov=fov)
        ObjectUtilsBlender._set_transform_keys_in_engine(obj_name=camera_name, transform_keys=transform_keys)

    @staticmethod
    def _spawn_shape_in_engine(
        type: str,
        transform_keys: 'Union[List[Dict], Dict]',
        shape_name: str = 'Shape',
        stencil_value: int = 1,
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
        """Spawn a shape in the engine.

        Args:
            type (str, enum in ['cube', 'plane', 'cone', 'cylinder', 'sphere', 'ico_sphere']): Type of the shape.
            transform_keys (Union[List[Dict], Dict]): Keyframes of transform (location, rotation, and scale).
            shape_name (str, optional): Name of the shape. Defaults to 'Shape'.
            stencil_value (int, optional): Stencil value of the shape. Defaults to 1.
            size (float in [0, inf], optional): Size. Defaults to 1.0. (unit: meter)
            segments (int in [3, 100000], optional): Segments. Defaults to 32.
            ring_count (int in [3, 100000], optional): Ring count. Defaults to 16.
            radius (float in [0, inf], optional): Radius. Defaults to 1.0. (unit: meter)
            subdivisions (int in [1, 10], optional): Subdivisions. Defaults to 2.
            vertices (int in [3, 10000000], optional): Vertices. Defaults to 32.
            depth (float in [0, inf], optional): Depth. Defaults to 2.0. (unit: meter)
            radius1 (float in [0, inf], optional): Radius1. Defaults to 0.0. (unit: meter)
            radius2 (float in [0, inf], optional): Radius2. Defaults to 2.0. (unit: meter)
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]

        ShapeBlenderWrapper._spawn_shape_in_engine(
            name=shape_name,
            type=type,
            size=size,
            segments=segments,
            ring_count=ring_count,
            radius=radius1,
            subdivisions=subdivisions,
            vertices=vertices,
            depth=depth,
            radius1=radius1,
            radius2=radius2,
        )
        ObjectUtilsBlender._set_transform_keys_in_engine(obj_name=shape_name, transform_keys=transform_keys)
        # XXX: set stencil value. may use actor property
        bpy.data.objects[shape_name].pass_index = stencil_value

    # -------- use methods -------- #
    @staticmethod
    def _use_camera_in_engine(
        transform_keys: 'Union[List[Dict], Dict]',
        fov: float = 90.0,
        camera_name: str = 'Camera',
    ) -> None:
        """Use level camera to render in the sequence in the engine.

        Args:
            camera_name (str): Name of the camera.
        """
        import math

        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]

        # get actor by name
        camera = bpy.data.objects[camera_name]

        # set sequence properties
        collection = XRFeitoriaBlenderFactory.get_active_collection()
        level_camera_data = collection.sequence_properties.level_cameras.add()
        level_camera_data.camera = camera
        level_camera_data.location = actor.location
        level_camera_data.rotation = actor.rotation_euler
        level_camera_data.scale = actor.scale
        level_camera_data.level_fov = camera.data.angle
        level_camera_data.sequence_fov = math.radians(fov)

        # set level camera's properties
        CameraBlender._set_camera_fov_in_engine(camera_name=camera_name, fov=fov)
        ObjectUtilsBlender._set_transform_keys_in_engine(obj_name=camera_name, transform_keys=transform_keys)
        level_camera_data.sequence_animation = camera.animation_data.action if actor.animation_data else None

        # set camera activity
        scene = XRFeitoriaBlenderFactory.get_active_scene()
        XRFeitoriaBlenderFactory.set_camera_activity(camera_name=camera_name, scene=scene, active=True)

    @staticmethod
    def _use_actor_in_engine(
        actor_name: str,
        transform_keys: 'Union[List[Dict], Dict]',
        stencil_value: int,
        anim_asset_path: 'Optional[str]' = None,
    ):
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]

        # get actor by name
        actor = bpy.data.objects[actor_name]

        # if anim_asset_path is None, use the current action of the actor if it has one
        # else, use the action of the anim_asset_path
        if anim_asset_path is None:
            if actor.animation_data and actor.animation_data.action:
                action = actor.animation_data.action
            else:
                action = None
        else:
            action = bpy.data.actions[anim_asset_path]

        # set sequence properties
        collection = XRFeitoriaBlenderFactory.get_active_collection()
        level_actor_data = collection.sequence_properties.level_actors.add()
        level_actor_data.actor = actor
        level_actor_data.level_stencil_value = actor.pass_index
        level_actor_data.sequence_stencil_value = stencil_value
        level_actor_data.level_animation = actor.animation_data.action if actor.animation_data else None
        level_actor_data.sequence_animation = action
        level_actor_data.location = actor.location
        level_actor_data.rotation = actor.rotation_euler
        level_actor_data.scale = actor.scale

        # set level actor's properties
        actor.pass_index = stencil_value
        if action:
            XRFeitoriaBlenderFactory.apply_action_to_actor(action=action, actor=actor)
        ObjectUtilsBlender._set_transform_keys_in_engine(obj_name=actor_name, transform_keys=transform_keys)
        level_actor_data.sequence_animation = actor.animation_data.action if actor.animation_data else None
