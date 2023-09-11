from typing import Dict, List, Literal, Optional, Tuple, Union

from loguru import logger

from ..actor.actor_unreal import ActorUnreal
from ..camera.camera_unreal import CameraUnreal
from ..data_structure.constants import PathLike, Vector
from ..object.object_utils import ObjectUtilsUnreal
from ..renderer.renderer_unreal import RendererUnreal
from ..rpc import remote_unreal
from ..utils.functions import unreal_functions
from .sequence_base import SequenceBase

try:
    import unreal
    from unreal_factory import XRFeitoriaUnrealFactory  # defined in src/XRFeitoriaUnreal/Content/Python
except ModuleNotFoundError:
    pass

try:
    from ..data_structure.models import RenderJobUnreal, RenderPass
    from ..data_structure.models import SequenceTransformKey as SeqTransKey
    from ..data_structure.models import TransformKeys
except ModuleNotFoundError:
    pass


@remote_unreal(dec_class=True, suffix='_in_engine')
class SequenceUnreal(SequenceBase):
    """Sequence class for Unreal."""

    _camera = CameraUnreal
    _object_utils = ObjectUtilsUnreal
    _renderer = RendererUnreal

    @classmethod
    def add_to_renderer(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: 'List[RenderPass]',
        file_name_format: str = '{sequence_name}/{render_pass}/{camera_name}/{frame_number}',
        console_variables: Dict[str, float] = {},
        anti_aliasing: 'Optional[RenderJobUnreal.AntiAliasSetting]' = None,
        export_vertices: bool = False,
        export_skeleton: bool = False,
    ) -> None:
        """Add the sequence to the renderer's job queue. Can only be called after the
        sequence is instantiated using
        :meth:`~xrfeitoria.sequence.sequence_wrapper.SequenceWrapperUnreal.new` or
        :meth:`~xrfeitoria.sequence.sequence_wrapper.SequenceWrapperUnreal.o pen`.

        Args:
            output_path (PathLike): The path where the rendered output will be saved.
            resolution (Tuple[int, int]): The resolution of the output.
            render_passes (List[RenderPass]): The list of render passes to be rendered.
            file_name_format (str, optional): The format of the output file name.
                Defaults to ``{sequence_name}/{render_pass}/{camera_name}/{frame_number}``.
            console_variables (Dict[str, float], optional): The console variables to be set before rendering. Defaults to {}.
                Ref to :ref:`FAQ-stencil-value` for details.
            anti_aliasing (Optional[RenderJobUnreal.AntiAliasSetting], optional):
                The anti-aliasing settings for the render job. Defaults to None.
            export_vertices (bool, optional): Whether to export vertices. Defaults to False.
            export_skeleton (bool, optional): Whether to export the skeleton. Defaults to False.

        Examples:
            >>> import xrfeitoria as xf
            >>> from xrfeitoria.data_structure.models import RenderPass
            >>> with xf.init_blender() as xf_runner:
            ...     seq = xf_runner.Sequence.new(seq_name='test'):
            ...         seq.add_to_renderer(
            ...             output_path=...,
            ...             resolution=...,
            ...             render_passes=[RenderPass('img', 'png')],
            ...         )
            ...     xf_runner.render()
        """
        map_path = SequenceUnreal._get_map_path_in_engine()
        sequence_path = SequenceUnreal._get_seq_path_in_engine()
        if anti_aliasing is None:
            anti_aliasing = RenderJobUnreal.AntiAliasSetting()
        cls._renderer.add_job(
            map_path=map_path,
            sequence_path=sequence_path,
            output_path=output_path,
            resolution=resolution,
            render_passes=render_passes,
            file_name_format=file_name_format,
            console_variables=console_variables,
            anti_aliasing=anti_aliasing,
            export_vertices=export_vertices,
            export_skeleton=export_skeleton,
        )
        logger.info(
            f'[cyan]Added[/cyan] sequence "{cls.name}" to [bold]`Renderer`[/bold] '
            f'(jobs to render: {len(cls._renderer.render_queue)})'
        )

    @classmethod
    def spawn_actor(
        cls,
        actor_asset_path: str,
        location: 'Vector',
        rotation: 'Vector',
        scale: 'Optional[Vector]' = None,
        actor_name: Optional[str] = None,
        stencil_value: int = 1,
        anim_asset_path: 'Optional[str]' = None,
    ) -> ActorUnreal:
        """Spawns an actor in the Unreal Engine at the specified location, rotation, and
        scale.

        Args:
            cls: The class object.
            actor_asset_path (str): The actor asset path in engine to spawn.
            location (Vector): The location to spawn the actor at. unit: meter.
            rotation (Vector): The rotation to spawn the actor with. unit: degree.
            scale (Optional[Vector], optional): The scale to spawn the actor with. Defaults to None.
            actor_name (Optional[str], optional): The name to give the spawned actor. Defaults to None.
            stencil_value (int in [0, 255], optional): The stencil value to use for the spawned actor. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.
            anim_asset_path (Optional[str], optional): The engine path to the animation asset of the actor. Defaults to None.

        Returns:
            ActorUnreal: The spawned actor object.
        """
        transform_keys = SeqTransKey(
            frame=0, location=location, rotation=rotation, scale=scale, interpolation='CONSTANT'
        )
        if actor_name is None:
            actor_name = cls._object_utils.generate_obj_name(obj_type='actor')
        cls._spawn_actor_in_engine(
            actor_asset_path=actor_asset_path,
            transform_keys=transform_keys.model_dump(),
            anim_asset_path=anim_asset_path,
            actor_name=actor_name,
            stencil_value=stencil_value,
        )
        logger.info(f'[cyan]Spawned[/cyan] actor "{actor_name}" in sequence "{cls.name}"')
        return ActorUnreal(actor_name)

    @classmethod
    def spawn_actor_with_keys(
        cls,
        actor_asset_path: str,
        transform_keys: 'TransformKeys',
        actor_name: Optional[str] = None,
        stencil_value: int = 1,
        anim_asset_path: 'Optional[str]' = None,
    ) -> ActorUnreal:
        """Spawns an actor in the Unreal Engine with the given asset path, transform
        keys, actor name, stencil value, and animation asset path.

        Args:
            actor_asset_path (str): The actor asset path in engine to spawn.
            transform_keys (TransformKeys): The transform keys of the actor.
            actor_name (Optional[str], optional): The name of the actor. Defaults to None.
            stencil_value (int in [0, 255], optional): The stencil value to use for the spawned actor. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.
            anim_asset_path (Optional[str], optional): The engine path to the animation asset of the actor. Defaults to None.

        Returns:
            ActorUnreal: The spawned actor.
        """
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]

        if actor_name is None:
            actor_name = cls._object_utils.generate_obj_name(obj_type='actor')

        cls._spawn_actor_in_engine(
            actor_asset_path=actor_asset_path,
            transform_keys=transform_keys,
            anim_asset_path=anim_asset_path,
            actor_name=actor_name,
            stencil_value=stencil_value,
        )
        logger.info(
            f'[cyan]Spawned[/cyan] actor "{actor_name}" with {len(transform_keys)} keys in sequence "{cls.name}"'
        )
        return ActorUnreal(actor_name)

    @classmethod
    def use_camera(
        cls,
        camera: CameraUnreal,
        location: 'Optional[Vector]' = None,
        rotation: 'Optional[Vector]' = None,
        fov: float = 90.0,
    ) -> None:
        """Uses the specified camera in the Unreal Engine sequence.

        Args:
            camera (CameraUnreal): The camera to use in the sequence.
            location (Optional[Vector], optional): The location of the camera. Defaults to None. unit: meter.
            rotation (Optional[Vector], optional): The rotation of the camera. Defaults to None. unit: degree.
            fov (float, optional): The field of view of the camera. Defaults to 90.0. unit: degree.
        """
        camera_name = camera.name
        transform_keys = SeqTransKey(frame=0, location=location, rotation=rotation, interpolation='CONSTANT')
        cls._use_camera_in_engine(
            transform_keys=transform_keys.model_dump(),
            fov=fov,
            camera_name=camera_name,
        )
        logger.info(f'[cyan]Used[/cyan] camera "{camera_name}" in sequence "{cls.name}"')

    @classmethod
    def use_camera_with_keys(
        cls,
        camera: CameraUnreal,
        transform_keys: 'TransformKeys',
        fov: float = 90.0,
    ) -> CameraUnreal:
        """Uses the specified camera in the Unreal Engine with the given transform keys
        and field of view.

        Args:
            camera (CameraUnreal): The camera to use.
            transform_keys (TransformKeys): The transform keys to use.
            fov (float, optional): The field of view to use. Defaults to 90.0. unit: degree.
        """
        camera_name = camera.name
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        cls._use_camera_in_engine(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )
        logger.info(
            f'[cyan]Used[/cyan] camera "{camera_name}" with {len(transform_keys)} keys in sequence "{cls.name}"'
        )

    @classmethod
    def use_actor(
        cls,
        actor: ActorUnreal,
        location: 'Optional[Vector]' = None,
        rotation: 'Optional[Vector]' = None,
        scale: 'Optional[Vector]' = None,
        stencil_value: int = 1,
        anim_asset_path: 'Optional[str]' = None,
    ) -> None:
        """Adds an actor to the sequence and sets its initial transform.

        Args:
            actor (ActorUnreal): The actor to add to the sequence.
            location (Optional[Vector]): The initial location of the actor. If None, the actor's current location is used. unit: meter.
            rotation (Optional[Vector]): The initial rotation of the actor. If None, the actor's current rotation is used. unit: degree.
            scale (Optional[Vector]): The initial scale of the actor. If None, the actor's current scale is used.
            stencil_value (int in [0, 255], optional): The stencil value to use for the spawned actor. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.
            anim_asset_path (Optional[str]): The engine path to the animation asset to use for the actor. If None, no animation is used.
        """
        actor_name = actor.name
        transform_keys = SeqTransKey(
            frame=0, location=location, rotation=rotation, scale=scale, interpolation='CONSTANT'
        )
        cls._use_actor_in_engine(
            actor_name=actor_name,
            transform_keys=transform_keys.model_dump(),
            stencil_value=stencil_value,
            anim_asset_path=anim_asset_path,
        )
        logger.info(f'[cyan]Used[/cyan] actor "{actor_name}" in sequence "{cls.name}"')

    @classmethod
    def use_actor_with_keys(
        cls,
        actor: ActorUnreal,
        transform_keys: 'TransformKeys',
        stencil_value: int = 1,
        anim_asset_path: 'Optional[str]' = None,
    ) -> None:
        """Uses the specified actor with the given transform keys in the Unreal Engine
        sequence.

        Args:
            actor (ActorUnreal): The actor to use in the sequence.
            transform_keys (Union[TransformKeys, List[TransformKeys]]): The transform keys to use with the actor.
            stencil_value (int in [0, 255], optional): The stencil value to use for the spawned actor. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.
            anim_asset_path (Optional[str], optional): The engine path to the animation asset to use. Defaults to None.
        """
        actor_name = actor.name
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        transform_keys = [i.model_dump() for i in transform_keys]
        cls._use_actor_in_engine(
            actor_name=actor_name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
            anim_asset_path=anim_asset_path,
        )
        logger.info(f'[cyan]Used[/cyan] actor "{actor_name}" with {len(transform_keys)} keys in sequence "{cls.name}"')

    @classmethod
    def get_map_path(cls) -> str:
        """Returns the path to the map corresponding to the sequence in the Unreal
        Engine.

        Returns:
            str: engine path to the map corresponding to the sequence.
        """
        return cls._get_map_path_in_engine()

    @classmethod
    def get_seq_path(cls) -> str:
        """Returns the path to the sequence in the Unreal Engine.

        Returns:
            str: engine path to the sequence.
        """
        return cls._get_seq_path_in_engine()

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _get_seq_info_in_engine(
        seq_name: str,
        seq_dir: 'Optional[str]' = None,
        map_path: 'Optional[str]' = None,
    ) -> 'Tuple[str, str]':
        _suffix = XRFeitoriaUnrealFactory.constants.data_asset_suffix
        default_sequence_path = XRFeitoriaUnrealFactory.constants.DEFAULT_SEQUENCE_PATH
        seq_dir = seq_dir or default_sequence_path  # default sequence path
        if map_path is None:
            seq_data_path = f'{seq_dir}/{seq_name}{_suffix}'
            unreal_functions.check_asset_in_engine(seq_data_path, raise_error=True)
            seq_path, map_path = XRFeitoriaUnrealFactory.Sequence.get_data_asset_info(seq_data_path)
        else:
            seq_path = f'{seq_dir}/{seq_name}'

        return seq_path, map_path

    @staticmethod
    def _get_map_path_in_engine() -> str:
        return XRFeitoriaUnrealFactory.Sequence.map_path

    @staticmethod
    def _get_seq_path_in_engine() -> str:
        return XRFeitoriaUnrealFactory.Sequence.sequence_path

    @staticmethod
    def _new_seq_in_engine(
        level: str,
        seq_name: str,
        seq_dir: 'Optional[str]' = None,
        seq_fps: 'Optional[float]' = None,
        seq_length: 'Optional[int]' = None,
        replace: bool = False,
    ) -> str:
        """Create a new sequence.

        Args:
            level (str): path of the map asset.
            seq_name (str): name of the sequence.
            seq_dir (Optional[str], optional): path of the sequence asset. Defaults to None.
            seq_fps (Optional[float], optional): FPS of the sequence. Defaults to None.
            seq_length (Optional[int], optional): length of the sequence. Defaults to None.
            replace (bool, optional): whether to replace the sequence if it already exists. Defaults to False.

        Returns:
            str: path of the data asset of sequence data, containing sequence_path and map_path.
        """
        return XRFeitoriaUnrealFactory.Sequence.new(
            map_path=level,
            seq_name=seq_name,
            seq_dir=seq_dir,
            seq_fps=seq_fps,
            seq_length=seq_length,
            replace=replace,
        )

    @staticmethod
    def _open_seq_in_engine(
        seq_name: str,
        seq_dir: 'Optional[str]' = None,
        map_path: 'Optional[str]' = None,
    ) -> None:
        seq_path, map_path = SequenceUnreal._get_seq_info_in_engine(
            seq_name=seq_name, seq_dir=seq_dir, map_path=map_path
        )
        XRFeitoriaUnrealFactory.Sequence.open(
            map_path=map_path,
            seq_path=seq_path,
        )

    @staticmethod
    def _save_seq_in_engine() -> None:
        XRFeitoriaUnrealFactory.Sequence.save()

    @staticmethod
    def _close_seq_in_engine() -> None:
        XRFeitoriaUnrealFactory.Sequence.close()

    @staticmethod
    def _show_seq_in_engine() -> None:
        XRFeitoriaUnrealFactory.Sequence.show()

    # ------ add actor and camera -------- #

    @staticmethod
    def _use_camera_in_engine(
        transform_keys: 'Union[List[Dict], Dict]',
        fov: float = 90.0,
        camera_name: str = 'Camera',
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.add_camera(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
        )

    @staticmethod
    def _use_actor_in_engine(
        actor_name: str,
        transform_keys: 'Union[List[Dict], Dict]',
        stencil_value: int = 1,
        anim_asset_path: 'Optional[str]' = None,
    ):
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.add_actor(
            actor_name=actor_name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
            animation_asset=anim_asset_path,
        )

    # ------ spawn actor and camera ------ #

    @staticmethod
    def _spawn_camera_in_engine(
        transform_keys: 'Union[List[Dict], Dict]',
        fov: float = 90.0,
        camera_name: str = 'Camera',
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.add_camera(
            transform_keys=transform_keys,
            fov=fov,
            camera_name=camera_name,
            spawnable=True,
        )

    @staticmethod
    def _spawn_actor_in_engine(
        actor_asset_path: str,
        transform_keys: 'Union[List[Dict], Dict]',
        anim_asset_path: 'Optional[str]' = None,
        actor_name: str = 'Actor',
        stencil_value: int = 1,
    ) -> None:
        # check asset
        unreal_functions.check_asset_in_engine(actor_asset_path, raise_error=True)
        if anim_asset_path is not None:
            unreal_functions.check_asset_in_engine(anim_asset_path, raise_error=True)

        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        XRFeitoriaUnrealFactory.Sequence.add_actor(
            actor=actor_asset_path,
            animation_asset=anim_asset_path,
            actor_name=actor_name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
        )

    @staticmethod
    def _spawn_shape_in_engine(
        type: 'Literal["plane", "cube", "sphere", "cylinder", "cone"]',
        transform_keys: 'Union[List[Dict], Dict]',
        shape_name: str = 'Shape',
        stencil_value: int = 1,
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        shape_path = XRFeitoriaUnrealFactory.constants.SHAPE_PATHS[type]
        XRFeitoriaUnrealFactory.Sequence.add_actor(
            actor=shape_path,
            animation_asset=None,
            actor_name=shape_name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
        )
