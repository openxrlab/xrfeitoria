import json
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, TypedDict, Union

from loguru import logger

from ..actor.actor_unreal import ActorUnreal
from ..camera.camera_unreal import CameraUnreal
from ..data_structure.constants import MotionFrame, PathLike, Vector
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
except (ImportError, ModuleNotFoundError):
    pass

dict_process_dir = TypedDict(
    'dict_process_dir',
    {
        'camera_dir': str,
        'actor_infos_dir': str,
        'vertices_dir': str,
        'skeleton_dir': str,
    },
)


@remote_unreal(dec_class=True, suffix='_in_engine')
class SequenceUnreal(SequenceBase):
    """Sequence class for Unreal."""

    _actor = ActorUnreal
    _camera = CameraUnreal
    _object_utils = ObjectUtilsUnreal
    _renderer = RendererUnreal

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
        self.close()

    @classmethod
    def save(cls) -> None:
        """Save the sequence."""
        cls._save_seq_in_engine()
        logger.info(f'++++  [cyan]Saved[/cyan] sequence "{cls.name}" ++++')

    @classmethod
    def show(cls) -> None:
        """Show the sequence in the engine."""
        cls._show_seq_in_engine()

    @classmethod
    def _preprocess_before_render(
        cls,
        save_dir: str,
        resolution: Tuple[int, int],
        export_vertices: bool,
        export_skeleton: bool,
    ) -> None:
        from ..camera.camera_parameter import CameraParameter

        for frame_idx in range(*cls.get_playback()):
            _dir_ = cls._preprocess_in_engine(
                save_dir=save_dir,
                per_frame=False,
                export_vertices=export_vertices,
                export_skeleton=export_skeleton,
                frame_idx=frame_idx,
            )

        # 1. convert camera parameters to xrprimer structure
        for file in Path(_dir_['camera_dir']).glob('*/*.json'):
            data = json.loads(file.read_text())
            cam_param = CameraParameter.from_unreal_convention(
                location=data['location'],
                rotation=data['rotation'],
                fov=data['fov'],
                image_size=resolution,
            )
            cam_param.dump(file.as_posix())  # replace the original file

        # TODO:
        # 2. convert actor infos from `.dat` to `.json`
        # 3. convert vertices from `.dat` to `.npz`
        # 4. convert skeleton from `.dat` to `.json`

    @classmethod
    def add_to_renderer(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],  # (width, height)
        render_passes: 'List[RenderPass]',
        file_name_format: str = '{sequence_name}/{render_pass}/{camera_name}/{frame_number}',
        console_variables: Dict[str, float] = {'r.MotionBlurQuality': 0},
        anti_aliasing: 'Optional[RenderJobUnreal.AntiAliasSetting]' = None,
        export_vertices: bool = False,
        export_skeleton: bool = False,
        export_audio: bool = False,
    ) -> None:
        """Add the sequence to the renderer's job queue. Can only be called after the
        sequence is instantiated using
        :meth:`~xrfeitoria.sequence.sequence_wrapper.SequenceWrapperUnreal.new` or
        :meth:`~xrfeitoria.sequence.sequence_wrapper.SequenceWrapperUnreal.open`.

        Args:
            output_path (PathLike): The path where the rendered output will be saved.
            resolution (Tuple[int, int]): The resolution of the output. (width, height)
            render_passes (List[RenderPass]): The list of render passes to be rendered.
            file_name_format (str, optional): The format of the output file name.
                Defaults to ``{sequence_name}/{render_pass}/{camera_name}/{frame_number}``.
            console_variables (Dict[str, float], optional): The console variables to be set before rendering. Defaults to {'r.MotionBlurQuality': 0}.
                Ref to :ref:`FAQ-stencil-value` for details.
            anti_aliasing (Optional[RenderJobUnreal.AntiAliasSetting], optional):
                The anti-aliasing settings for the render job. Defaults to None.
            export_vertices (bool, optional): Whether to export vertices. Defaults to False.
            export_skeleton (bool, optional): Whether to export the skeleton. Defaults to False.
            export_audio (bool, optional): Whether to export audio. Defaults to False.

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

        msg = 'Preprocessing before rendering, including exporting camera parameters'
        if export_vertices:
            msg += ', vertices'
        if export_skeleton:
            msg += ', skeleton'
        logger.info(msg)
        cls._preprocess_before_render(
            save_dir=f'{output_path}/{cls.name}',
            resolution=resolution,
            export_vertices=export_vertices,
            export_skeleton=export_skeleton,
        )

        cls._renderer.add_job(
            map_path=map_path,
            sequence_path=sequence_path,
            output_path=output_path,
            resolution=resolution,
            render_passes=render_passes,
            file_name_format=file_name_format,
            console_variables=console_variables,
            anti_aliasing=anti_aliasing,
            export_audio=export_audio,
        )

        logger.info(
            f'[cyan]Added[/cyan] sequence "{cls.name}" to [bold]`Renderer`[/bold] '
            f'(jobs to render: {len(cls._renderer.render_queue)})'
        )

    @classmethod
    def spawn_actor(
        cls,
        actor_asset_path: str,
        location: 'Optional[Vector]' = None,
        rotation: 'Optional[Vector]' = None,
        scale: 'Optional[Vector]' = None,
        actor_name: Optional[str] = None,
        stencil_value: int = 1,
        anim_asset_path: 'Optional[str]' = None,
        motion_data: 'Optional[List[MotionFrame]]' = None,
    ) -> ActorUnreal:
        """Spawns an actor in the Unreal Engine at the specified location, rotation, and
        scale.

        Args:
            cls: The class object.
            actor_asset_path (str): The actor asset path in engine to spawn.
            location (Optional[Vector, optional]): The location to spawn the actor at. unit: meter.
            rotation (Optional[Vector, optional]): The rotation to spawn the actor with. unit: degree.
            scale (Optional[Vector], optional): The scale to spawn the actor with. Defaults to None.
            actor_name (Optional[str], optional): The name to give the spawned actor. Defaults to None.
            stencil_value (int in [0, 255], optional): The stencil value to use for the spawned actor. Defaults to 1.
                Ref to :ref:`FAQ-stencil-value` for details.
            anim_asset_path (Optional[str], optional): The engine path to the animation asset of the actor. Defaults to None.
            motion_data (Optional[List[MotionFrame]]): The motion data used for FK animation.

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
            motion_data=motion_data,
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
        motion_data: 'Optional[List[MotionFrame]]' = None,
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
            motion_data (Optional[List[MotionFrame]]): The motion data used for FK animation.

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
            motion_data=motion_data,
            actor_name=actor_name,
            stencil_value=stencil_value,
        )
        logger.info(
            f'[cyan]Spawned[/cyan] actor "{actor_name}" with {len(transform_keys)} keys in sequence "{cls.name}"'
        )
        return ActorUnreal(actor_name)

    @classmethod
    def add_audio(
        cls,
        audio_asset_path: str,
        start_frame: Optional[int] = None,
        end_frame: Optional[int] = None,
    ) -> None:
        """Add an audio track to the sequence.

        Args:
            audio_asset_path (str): The path to the audio asset in the engine.
            start_frame (Optional[int], optional): The start frame of the audio track. Defaults to None.
            end_frame (Optional[int], optional): The end frame of the audio track. Defaults to None.
        """
        cls._add_audio_in_engine(audio_asset_path=audio_asset_path, start_frame=start_frame, end_frame=end_frame)

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

    @classmethod
    def set_playback(cls, start_frame: Optional[int] = None, end_frame: Optional[int] = None) -> None:
        """Set the playback range for the sequence.

        Args:
            start_frame (Optional[int]): The start frame of the playback range. If not provided, the default start frame will be used.
            end_frame (Optional[int]): The end frame of the playback range. If not provided, the default end frame will be used.

        Returns:
            None
        """
        cls._set_playback_in_engine(start_frame=start_frame, end_frame=end_frame)

    @classmethod
    def get_playback(cls) -> Tuple[int, int]:
        """Get the playback range for the sequence.

        Returns:
            Tuple[int, int]: The start and end frame of the playback range.
        """
        return cls._get_playback_in_engine()

    @classmethod
    def set_camera_cut_playback(cls, start_frame: Optional[int] = None, end_frame: Optional[int] = None) -> None:
        """Set the playback range for the sequence.

        Args:
            start_frame (Optional[int]): The start frame of the playback range. If not provided, the default start frame will be used.
            end_frame (Optional[int]): The end frame of the playback range. If not provided, the default end frame will be used.

        Returns:
            None
        """
        cls._set_camera_cut_player_in_engine(start_frame=start_frame, end_frame=end_frame)

    @classmethod
    def _open(cls, seq_name: str, seq_dir: 'Optional[str]' = None) -> None:
        """Open an exist sequence.

        Args:
            seq_name (str): Name of the sequence.
            seq_dir (Optional[str], optional): Path of the sequence.
                Defaults to None and fallback to the default path '/Game/XRFeitoriaUnreal/Sequences'.
        """
        cls._open_seq_in_engine(seq_name=seq_name, seq_dir=seq_dir)
        cls.name = seq_name
        logger.info(f'>>>> [cyan]Opened[/cyan] sequence "{cls.name}" >>>>')

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _get_default_seq_path_in_engine() -> str:
        return XRFeitoriaUnrealFactory.constants.DEFAULT_SEQUENCE_PATH

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
    def _preprocess_in_engine(
        save_dir: str,
        per_frame: bool = False,
        export_vertices: bool = False,
        export_skeleton: bool = False,
        frame_idx: 'Optional[int]' = None,
    ) -> 'dict_process_dir':
        """Preprocesses the sequence in the Unreal Engine.

        Args:
            save_dir (str): The directory to save the processed sequence.
            per_frame (bool, optional): Whether to process the sequence per frame. Defaults to False.
            export_vertices (bool, optional): Whether to export the vertices. Defaults to False.
            export_skeleton (bool, optional): Whether to export the skeleton. Defaults to False.
            frame_idx (Optional[int], optional): The index of the frame to process. Defaults to None.

        Returns:
            dict_process_dir: The directory paths of the saved data.
        """
        return XRFeitoriaUnrealFactory.Sequence.save_params(
            save_dir=save_dir,
            per_frame=per_frame,
            export_vertices=export_vertices,
            export_skeleton=export_skeleton,
            frame_idx=frame_idx,
        )

    @staticmethod
    def _new_seq_in_engine(
        seq_name: str,
        level: 'Optional[str]' = None,
        seq_dir: 'Optional[str]' = None,
        seq_fps: 'Optional[float]' = None,
        seq_length: 'Optional[int]' = None,
        replace: bool = False,
    ) -> str:
        """Create a new sequence.

        Args:
            seq_name (str): name of the sequence.
            level (Optional[str], optional): path of the map asset. Defaults to None.
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

    @staticmethod
    def _set_playback_in_engine(start_frame: 'Optional[int]' = None, end_frame: 'Optional[int]' = None) -> None:
        XRFeitoriaUnrealFactory.Sequence.set_playback(start_frame=start_frame, end_frame=end_frame)

    @staticmethod
    def _get_playback_in_engine() -> 'Tuple[int, int]':
        return XRFeitoriaUnrealFactory.Sequence.get_playback()

    @staticmethod
    def _set_camera_cut_player_in_engine(
        start_frame: 'Optional[int]' = None, end_frame: 'Optional[int]' = None
    ) -> None:
        XRFeitoriaUnrealFactory.Sequence.set_camera_cut_playback(start_frame=start_frame, end_frame=end_frame)

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
    def _import_actor_in_engine(
        file_path: str,
        transform_keys: 'Union[List[Dict], Dict]',
        actor_name: str = 'Actor',
        stencil_value: int = 1,
    ) -> None:
        if not isinstance(transform_keys, list):
            transform_keys = [transform_keys]
        if isinstance(transform_keys[0], dict):
            transform_keys = [XRFeitoriaUnrealFactory.constants.SequenceTransformKey(**k) for k in transform_keys]

        actor_path = XRFeitoriaUnrealFactory.utils.import_asset(file_path)
        logger.info(f'actor_path: {actor_path}')
        animation_asset_path = f'{actor_path[0]}_Anim'
        if not unreal.EditorAssetLibrary.does_asset_exist(animation_asset_path):
            animation_asset_path = None
        XRFeitoriaUnrealFactory.Sequence.add_actor(
            actor=actor_path[0],
            animation_asset=animation_asset_path,
            actor_name=actor_name,
            transform_keys=transform_keys,
            stencil_value=stencil_value,
        )

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
        motion_data: 'Optional[List[MotionFrame]]' = None,
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
            motion_data=motion_data,
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

    # ------ add audio -------- #
    @staticmethod
    def _add_audio_in_engine(
        audio_asset_path: str,
        start_frame: 'Optional[int]' = None,
        end_frame: 'Optional[int]' = None,
    ):
        # check asset
        unreal_functions.check_asset_in_engine(audio_asset_path, raise_error=True)
        XRFeitoriaUnrealFactory.Sequence.add_audio(
            audio_asset=audio_asset_path,
            start_frame=start_frame,
            end_frame=end_frame,
        )
