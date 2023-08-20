from typing import Any, Dict, List, NoReturn, Optional, Tuple, Union

import unreal
import utils_actor
import utils_sequencer
from constants import DEFAULT_SEQUENCE_PATH, SequenceTransformKey


class Sequence:
    map_path = None
    sequence_path = None
    sequence: unreal.LevelSequence = None
    bindings: Dict[str, Dict[str, Any]] = {}

    def __init__(self) -> NoReturn:
        raise Exception("Sequence (XRFeitoriaUnreal/Python) should not be instantiated")

    @classmethod
    def save(cls) -> None:
        if cls.sequence is not None:
            unreal.EditorAssetLibrary.save_loaded_asset(cls.sequence, False)

    @classmethod
    def close(cls) -> None:
        if cls.sequence is not None:
            unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()

            del cls.sequence
        cls.map_path = None
        cls.sequence_path = None
        cls.sequence = None
        cls.bindings = {}

    @classmethod
    def open(
        cls,
        map_path: str,
        seq_name: str,
        seq_dir: "Optional[str]" = None,
    ) -> None:
        assert unreal.EditorAssetLibrary.does_asset_exist(map_path), f"Map `{map_path}` does not exist"
        assert unreal.EditorAssetLibrary.does_asset_exist(
            f"{seq_dir}/{seq_name}"
        ), f"Sequence `{seq_dir}/{seq_name}` does not exist"

        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        cls.map_path = map_path
        if seq_dir is None:
            seq_dir = DEFAULT_SEQUENCE_PATH
        cls.sequence_path = f"{seq_dir}/{seq_name}"
        cls.sequence: unreal.LevelSequence = unreal.load_asset(cls.sequence_path)

    @classmethod
    def new(
        cls,
        map_path: str,
        seq_name: str,
        seq_dir: "Optional[str]" = None,
        seq_fps: "Optional[float]" = None,
        seq_length: "Optional[int]" = None,
        replace: bool = False,
    ) -> None:
        assert unreal.EditorAssetLibrary.does_asset_exist(map_path), f"Map `{map_path}` does not exist"
        if unreal.EditorAssetLibrary.does_asset_exist(f"{seq_dir}/{seq_name}"):
            if replace:
                unreal.EditorAssetLibrary.delete_asset(f"{seq_dir}/{seq_name}")
            else:
                raise Exception(f"Sequence `{seq_dir}/{seq_name}` already exists, use `replace=True` to replace it")

        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        cls.map_path = map_path
        if seq_dir is None:
            seq_dir = DEFAULT_SEQUENCE_PATH
        cls.sequence = utils_sequencer.generate_sequence(
            sequence_dir=seq_dir,
            sequence_name=seq_name,
            seq_fps=seq_fps,
            seq_length=seq_length,
        )
        cls.sequence_path = f"{seq_dir}/{seq_name}"

    @classmethod
    def show(cls) -> None:
        assert cls.sequence is not None, "Sequence not initialized"
        unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(cls.sequence)

    # ------ add actor and camera -------- #

    @classmethod
    def add_camera(
        cls,
        transform_keys: "Optional[Union[List[SequenceTransformKey], SequenceTransformKey]]" = None,
        fov: float = 90.0,
        camera_name: str = "Camera",
    ):
        camera = utils_actor.get_actor_by_name(camera_name)
        bindings = utils_sequencer.add_camera_to_sequence(
            sequence=cls.sequence,
            camera=camera,
            camera_transform_keys=transform_keys,
            camera_fov=fov,
        )
        cls.bindings[camera_name] = bindings

    @classmethod
    def add_actor(
        cls,
        actor_name: str,
        transform_keys: "Optional[Union[List[SequenceTransformKey], SequenceTransformKey]]" = None,
        actor_stencil_value: int = 1,
        animation_asset: "Optional[Union[str, unreal.AnimSequence]]" = None,
    ) -> None:
        assert cls.sequence is not None, "Sequence not initialized"
        if animation_asset and isinstance(animation_asset, str):
            animation_asset = unreal.load_asset(animation_asset)

        actor = utils_actor.get_actor_by_name(actor_name)
        bindings = utils_sequencer.add_actor_to_sequence(
            sequence=cls.sequence,
            actor=actor,
            actor_transform_keys=transform_keys,
            actor_stencil_value=actor_stencil_value,
            animation_asset=animation_asset,
        )
        cls.bindings[actor_name] = bindings

    # ------ spawn actor and camera ------ #

    @classmethod
    def spawn_camera(
        cls,
        transform_keys: "Optional[Union[List[SequenceTransformKey], SequenceTransformKey]]" = None,
        fov: float = 90.0,
        camera_name: str = "Camera",
    ) -> None:
        """
        Spawn a camera in sequence

        Args:
            transform_keys (Optional[Union[List[SequenceTransformKey], SequenceTransformKey]], optional): List of transform keys. Defaults to None.
            fov (float, optional): Field of view of camera. Defaults to 90.0.
            camera_name (str, optional): Name of camera to set in sequence. Defaults to "Camera".
        """
        assert cls.sequence is not None, "Sequence not initialized"
        bindings = utils_sequencer.add_spawnable_camera_to_sequence(
            sequence=cls.sequence,
            camera_name=camera_name,
            camera_transform_keys=transform_keys,
            camera_fov=fov,
        )
        cls.bindings[camera_name] = bindings

    @classmethod
    def spawn_actor(
        cls,
        actor: "Union[str, unreal.Actor]",
        animation_asset: "Optional[Union[str, unreal.AnimSequence]]" = None,
        actor_name: str = "Actor",
        transform_keys: "Optional[Union[List[SequenceTransformKey], SequenceTransformKey]]" = None,
        actor_stencil_value: int = 1,
    ) -> None:
        """
        Spawn an actor in sequence

        Args:
            actor (Union[str, unreal.Actor]): actor path (e.g. '/Game/Cube') / loaded asset (via `unreal.load_asset('/Game/Cube')`)
            animation_asset (Union[str, unreal.AnimSequence]): animation path (e.g. '/Game/Anim') / loaded asset (via `unreal.load_asset('/Game/Anim')`). Can be None which means no animation.
            actor_name (str, optional): Name of actor to set in sequence. Defaults to "Actor".
            transform_keys (Union[List[SequenceTransformKey], SequenceTransformKey], optional): List of transform keys. Defaults to None.
            actor_stencil_value (int, optional): Stencil value of actor, used for specifying the mask color for this actor (mask id). Defaults to 1.
        """
        assert cls.sequence is not None, "Sequence not initialized"
        if isinstance(actor, str):
            actor = unreal.load_asset(actor)
        if animation_asset and isinstance(animation_asset, str):
            animation_asset = unreal.load_asset(animation_asset)

        bindings = utils_sequencer.add_spawnable_actor_to_sequence(
            sequence=cls.sequence,
            actor_name=actor_name,
            actor_asset=actor,
            animation_asset=animation_asset,
            actor_transform_keys=transform_keys,
            actor_stencil_value=actor_stencil_value,
        )
        cls.bindings[actor_name] = bindings


if __name__ == "__main__":
    Sequence.new('/Game/NewMap', "test1")
    Sequence.spawn_camera(transform_keys=SequenceTransformKey(frame=0, location=(0, 0, 0), rotation=(0, 0, 0)))
    Sequence.spawn_actor(
        '/Game/StarterContent/Props/SM_Chair',
        transform_keys=SequenceTransformKey(frame=0, location=(0, 0, 0), rotation=(0, 0, 0)),
    )
