from typing import Any, Dict, List, NoReturn, Optional, Tuple, Type, Union

import unreal
import utils_actor
from constants import (
    DEFAULT_SEQUENCE_DATA_ASSET,
    DEFAULT_SEQUENCE_PATH,
    ENGINE_MAJOR_VERSION,
    SequenceTransformKey,
    SubSystem,
    TransformKeys,
    data_asset_suffix,
)
from utils import add_levels, get_levels, get_soft_object_path, get_world, new_world, save_current_level
from utils_actor import get_actor_mesh_component

EditorLevelSequenceSub = SubSystem.EditorLevelSequenceSub
EditorAssetSub = SubSystem.EditorAssetSub
EditorLevelSub = SubSystem.EditorLevelSub
START_FRAME = -1

################################################################################
# misc


def duplicate_binding(binding: unreal.SequencerBindingProxy) -> None:
    """For opening sequencer editor use `unreal.LevelSequenceEditorBlueprintLib
    rary.open_level_sequence(unreal.LevelSequence)` to open."""
    exported_txt = EditorLevelSequenceSub.copy_bindings([binding])
    EditorLevelSequenceSub.paste_bindings(exported_txt, unreal.MovieScenePasteBindingsParams())
    # TODO: the event track would be lost after pasting, need to fix it


def convert_frame_rate_to_fps(frame_rate: unreal.FrameRate) -> float:
    return frame_rate.numerator / frame_rate.denominator


def get_sequence_fps(sequence: unreal.LevelSequence) -> float:
    seq_fps: unreal.FrameRate = sequence.get_display_rate()
    return convert_frame_rate_to_fps(seq_fps)


def get_animation_length(animation_asset: unreal.AnimSequence, seq_fps: float = 30.0) -> int:
    if ENGINE_MAJOR_VERSION == 5:
        # animation fps == sequence fps
        anim_frame_rate = animation_asset.get_editor_property('target_frame_rate')
        anim_frame_rate = convert_frame_rate_to_fps(anim_frame_rate)
        assert (
            anim_frame_rate == seq_fps
        ), f'anim fps {anim_frame_rate} != seq fps {seq_fps}, this would cause animation interpolation.'

        anim_len = animation_asset.get_editor_property('number_of_sampled_frames')

    elif ENGINE_MAJOR_VERSION == 4:
        anim_len = round(animation_asset.get_editor_property('sequence_length') * seq_fps)

    return anim_len


################################################################################
# sequencer session
def find_binding_by_name(sequence: unreal.LevelSequence, name: str) -> unreal.SequencerBindingProxy:
    binding = sequence.find_binding_by_name(name=name)
    if binding.sequence is not None:
        return binding

    for binding in sequence.get_bindings():
        if binding.get_name() == name:
            return binding
    raise RuntimeError(f'Failed to find binding: {name}')


def get_time(sequence: unreal.LevelSequence, frame: int) -> unreal.FrameNumber:
    """Initialize a FrameNumber from the given time and then convert it to a FrameTime
    with no sub-frame.

    Keys can only exist on whole FrameNumbers.
        And transform from our Display Rate to the internal tick resolution.
    Note: equals to multiply 800
    """
    time_as_frame_time = unreal.FrameTime(unreal.FrameNumber(frame))
    frame_time = unreal.TimeManagementLibrary.transform_time(
        time_as_frame_time, sequence.get_display_rate(), sequence.get_tick_resolution()
    )
    return unreal.FrameNumber(frame_time.frame_number.value)


def get_value_from_channel(channel: unreal.MovieSceneScriptingFloatChannel) -> float:
    # XXX: hardcode for first key
    key: unreal.MovieSceneScriptingDoubleAsFloatKey = channel.get_keys()[0]
    return key.get_value()


def get_transform_channels_from_section(
    trans_section: unreal.MovieScene3DTransformSection,
) -> List[unreal.MovieSceneScriptingChannel]:
    (
        channel_x,
        channel_y,
        channel_z,
    ) = (
        channel_roll,
        channel_pitch,
        channel_yaw,
    ) = (
        channel_scale_x,
        channel_scale_y,
        channel_scale_z,
    ) = (None, None, None)
    for channel in trans_section.get_all_channels():
        channel: unreal.MovieSceneScriptingChannel
        if channel.channel_name == 'Location.X':
            channel_x = channel
        elif channel.channel_name == 'Location.Y':
            channel_y = channel
        elif channel.channel_name == 'Location.Z':
            channel_z = channel
        elif channel.channel_name == 'Rotation.X':
            channel_roll = channel
        elif channel.channel_name == 'Rotation.Y':
            channel_pitch = channel
        elif channel.channel_name == 'Rotation.Z':
            channel_yaw = channel
        elif channel.channel_name == 'Scale.X':
            channel_scale_x = channel
        elif channel.channel_name == 'Scale.Y':
            channel_scale_y = channel
        elif channel.channel_name == 'Scale.Z':
            channel_scale_z = channel

    assert channel_x is not None
    assert channel_y is not None
    assert channel_z is not None
    assert channel_roll is not None
    assert channel_pitch is not None
    assert channel_yaw is not None
    assert channel_scale_x is not None
    assert channel_scale_y is not None
    assert channel_scale_z is not None

    return (
        channel_x,
        channel_y,
        channel_z,
        channel_roll,
        channel_pitch,
        channel_yaw,
        channel_scale_x,
        channel_scale_y,
        channel_scale_z,
    )


def set_transforms_by_section(
    trans_section: unreal.MovieScene3DTransformSection,
    trans_keys: Union[Dict, SequenceTransformKey, List[SequenceTransformKey], List[Dict]],
) -> None:
    """Set `loc & rot` keys to given `transform section`

    Args:
        trans_section (unreal.MovieScene3DTransformSection): section
        trans_keys (Union[SequenceTransformKey, List[SequenceTransformKey]]):
            transform keys, contains frame, location, rotation and interpolation

    Examples:
        >>> sequence = unreal.load_asset('/Game/Sequences/NewSequence')
        ... camera_binding = sequence.add_spawnable_from_class(unreal.CameraActor)
        ... transform_track: unreal.MovieScene3DTransformTrack = camera_binding.add_track(unreal.MovieScene3DTransformTrack)
        ... transform_section: unreal.MovieScene3DTransformSection = transform_track.add_section()
        ... set_transforms_by_section(transform_section, [
        ...     SequenceTransformKey(frame=0, location=(0, 0, 0), rotation=(0, 0, 0), interpolation='CONSTANT'),
        ... ])
    """
    (
        channel_x,
        channel_y,
        channel_z,
        channel_roll,
        channel_pitch,
        channel_yaw,
        channel_scale_x,
        channel_scale_y,
        channel_scale_z,
    ) = get_transform_channels_from_section(trans_section)

    if not isinstance(trans_keys, (list, tuple)):
        trans_keys = [trans_keys]
    if isinstance(trans_keys[0], dict):
        trans_keys = [SequenceTransformKey(**k) for k in trans_keys]

    for trans_key in trans_keys:
        trans_key: SequenceTransformKey
        key_frame = trans_key.frame
        key_type = trans_key.interpolation.value
        key_type_ = getattr(unreal.MovieSceneKeyInterpolation, key_type)

        key_time_ = unreal.FrameNumber(key_frame)
        if trans_key.location:
            loc_x, loc_y, loc_z = trans_key.location
            channel_x.add_key(key_time_, loc_x, interpolation=key_type_)
            channel_y.add_key(key_time_, loc_y, interpolation=key_type_)
            channel_z.add_key(key_time_, loc_z, interpolation=key_type_)
        if trans_key.rotation:
            rot_x, rot_y, rot_z = trans_key.rotation
            channel_roll.add_key(key_time_, rot_x, interpolation=key_type_)
            channel_pitch.add_key(key_time_, rot_y, interpolation=key_type_)
            channel_yaw.add_key(key_time_, rot_z, interpolation=key_type_)
        if trans_key.scale:
            scale_x, scale_y, scale_z = trans_key.scale
            channel_scale_x.add_key(key_time_, scale_x, interpolation=key_type_)
            channel_scale_y.add_key(key_time_, scale_y, interpolation=key_type_)
            channel_scale_z.add_key(key_time_, scale_z, interpolation=key_type_)


def set_animation_by_section(
    animation_section: unreal.MovieSceneSkeletalAnimationSection,
    animation_asset: unreal.SkeletalMesh,
    animation_length: Optional[int] = None,
    seq_fps: int = 30,
) -> None:
    animation_length_ = get_animation_length(animation_asset, seq_fps)
    if animation_length is None:
        animation_length = animation_length_
    if animation_length > animation_length_:
        unreal.log_error(f"animation: '{animation_asset.get_name()}' length is too short, it will repeat itself!")

    params = unreal.MovieSceneSkeletalAnimationParams()
    params.set_editor_property('Animation', animation_asset)
    animation_section.set_editor_property('Params', params)
    animation_section.set_range(0, animation_length)


def add_property_bool_track_to_binding(
    binding: unreal.SequencerBindingProxy,
    property_name: str,
    property_value: bool,
) -> Tuple[unreal.MovieSceneBoolTrack, unreal.MovieSceneBoolSection]:
    # add bool track
    bool_track: unreal.MovieSceneBoolTrack = binding.add_track(unreal.MovieSceneBoolTrack)
    bool_track.set_property_name_and_path(property_name, property_name)

    # add bool section, and set it to extend the whole sequence
    bool_section = bool_track.add_section()
    bool_section.set_start_frame_bounded(0)
    bool_section.set_end_frame_bounded(0)

    # set key
    for channel in bool_section.find_channels_by_type(unreal.MovieSceneScriptingBoolChannel):
        channel.set_default(property_value)

    return bool_track, bool_section


def add_property_int_track_to_binding(
    binding: unreal.SequencerBindingProxy,
    property_name: str,
    property_value: int,
) -> Tuple[unreal.MovieSceneIntegerTrack, unreal.MovieSceneIntegerSection]:
    # add int track
    int_track: unreal.MovieSceneIntegerTrack = binding.add_track(unreal.MovieSceneIntegerTrack)
    int_track.set_property_name_and_path(property_name, property_name)

    # add int section, and set it to extend the whole sequence
    int_section = int_track.add_section()
    int_section.set_start_frame_bounded(0)
    int_section.set_end_frame_bounded(0)

    # set key
    for channel in int_section.find_channels_by_type(unreal.MovieSceneScriptingIntegerChannel):
        channel.set_default(property_value)

    return int_track, int_section


def add_property_string_track_to_binding(
    binding: unreal.SequencerBindingProxy,
    property_name: str,
    property_value: Union[str, Dict[int, str]],
) -> Tuple[unreal.MovieSceneStringTrack, unreal.MovieSceneStringSection]:
    # add string track
    string_track: unreal.MovieSceneStringTrack = binding.add_track(unreal.MovieSceneStringTrack)
    string_track.set_property_name_and_path(property_name, property_name)

    # add int section, and set it to extend the whole sequence
    string_section = string_track.add_section()
    string_section.set_start_frame_bounded(0)
    string_section.set_end_frame_bounded(0)

    # set key
    for channel in string_section.find_channels_by_type(unreal.MovieSceneScriptingStringChannel):
        channel: unreal.MovieSceneScriptingStringChannel
        if isinstance(property_value, str):
            channel.set_default(property_value)
        elif isinstance(property_value, dict):
            for key_frame, value in property_value.items():
                channel.add_key(unreal.FrameNumber(key_frame), value)

    return string_track, string_section


def add_property_float_track_to_binding(
    binding: unreal.SequencerBindingProxy,
    property_name: str,
    property_value: float,
) -> Tuple[unreal.MovieSceneFloatTrack, unreal.MovieSceneFloatSection]:
    # add float track
    float_track: unreal.MovieSceneFloatTrack = binding.add_track(unreal.MovieSceneFloatTrack)
    float_track.set_property_name_and_path(property_name, property_name)

    # add float section, and set it to extend the whole sequence
    float_section = float_track.add_section()
    float_section.set_start_frame_bounded(0)
    float_section.set_end_frame_bounded(0)

    # set key
    for channel in float_section.get_channels_by_type(unreal.MovieSceneScriptingFloatChannel):
        channel.set_default(property_value)

    return float_section, float_section


def add_or_find_transform_track_to_binding(
    binding: unreal.SequencerBindingProxy,
) -> Tuple[unreal.MovieScene3DTransformTrack, unreal.MovieScene3DTransformSection]:
    # find transform track
    transform_track = binding.find_tracks_by_type(unreal.MovieScene3DTransformTrack)
    if len(transform_track) > 0:
        transform_track = transform_track[0]
        transform_section = transform_track.get_sections()[0]
        return transform_track, transform_section

    transform_track: unreal.MovieScene3DTransformTrack = binding.add_track(unreal.MovieScene3DTransformTrack)
    transform_section: unreal.MovieScene3DTransformSection = transform_track.add_section()
    # set infinite
    transform_section.set_start_frame_bounded(0)
    transform_section.set_end_frame_bounded(0)

    return transform_track, transform_section


def add_or_find_anim_track_to_binding(
    binding: unreal.SequencerBindingProxy,
) -> Tuple[unreal.MovieSceneSkeletalAnimationTrack, unreal.MovieSceneSkeletalAnimationSection]:
    animation_track = binding.find_tracks_by_type(unreal.MovieSceneSkeletalAnimationTrack)
    if len(animation_track) > 0:
        animation_track = animation_track[0]
        animation_section = animation_track.get_sections()[0]
        return animation_track, animation_section

    animation_track: unreal.MovieSceneSkeletalAnimationTrack = binding.add_track(
        track_type=unreal.MovieSceneSkeletalAnimationTrack
    )
    animation_section: unreal.MovieSceneSkeletalAnimationSection = animation_track.add_section()
    # set infinite
    animation_section.set_start_frame_bounded(0)
    animation_section.set_end_frame_bounded(0)
    return animation_track, animation_section


def add_transforms_to_binding(
    binding: unreal.SequencerBindingProxy,
    actor_trans_keys: Union[SequenceTransformKey, List[SequenceTransformKey]],
):
    _, transform_section = add_or_find_transform_track_to_binding(binding)
    # add keys
    set_transforms_by_section(transform_section, actor_trans_keys)


def add_animation_to_binding(
    binding: unreal.SequencerBindingProxy,
    animation_asset: unreal.AnimSequence,
    animation_length: Optional[int] = None,
    seq_fps: Optional[float] = None,
) -> None:
    _, animation_section = add_or_find_anim_track_to_binding(binding)
    set_animation_by_section(animation_section, animation_asset, animation_length, seq_fps)


def get_spawnable_actor_from_binding(
    sequence: unreal.MovieSceneSequence,
    binding: unreal.SequencerBindingProxy,
) -> unreal.Actor:
    binds = unreal.Array(unreal.SequencerBindingProxy)
    binds.append(binding)

    bound_objects: List[unreal.SequencerBoundObjects] = unreal.SequencerTools.get_bound_objects(
        get_world(), sequence, binds, sequence.get_playback_range()
    )

    actor = bound_objects[0].bound_objects[0]
    return actor


################################################################################
# high level functions


def add_level_visibility_to_sequence(
    sequence: unreal.LevelSequence,
    seq_length: Optional[int] = None,
) -> None:
    if seq_length is None:
        seq_length = sequence.get_playback_end()

    # add master track (level visibility) to sequence
    level_visibility_track: unreal.MovieSceneLevelVisibilityTrack = sequence.add_master_track(
        unreal.MovieSceneLevelVisibilityTrack
    )
    # add level visibility section
    level_visible_section: unreal.MovieSceneLevelVisibilitySection = level_visibility_track.add_section()
    level_visible_section.set_visibility(unreal.LevelVisibility.VISIBLE)
    level_visible_section.set_start_frame(START_FRAME)
    level_visible_section.set_end_frame(seq_length)

    level_hidden_section: unreal.MovieSceneLevelVisibilitySection = level_visibility_track.add_section()
    level_hidden_section.set_row_index(1)
    level_hidden_section.set_visibility(unreal.LevelVisibility.HIDDEN)
    level_hidden_section.set_start_frame(START_FRAME)
    level_hidden_section.set_end_frame(seq_length)
    return level_visible_section, level_hidden_section


def add_level_to_sequence(
    sequence: unreal.LevelSequence,
    persistent_level_path: str,
    new_level_path: str,
    seq_fps: Optional[float] = None,
    seq_length: Optional[int] = None,
) -> None:
    """Creating a new level which contains the persistent level as sub-levels.
    `CAUTION`: this function can't support `World Partition` type level which is new in
    unreal 5. No warning/error would be printed if `World partition` is used, but it
    will not work.

    Args:
        sequence (unreal.LevelSequence): _description_
        persistent_level_path (str): _description_
        new_level_path (str): _description_
        seq_fps (Optional[float], optional): _description_. Defaults to None.
        seq_length (Optional[int], optional): _description_. Defaults to None.
    """

    # get sequence settings
    if seq_fps is None:
        seq_fps = get_sequence_fps(sequence)
    if seq_length is None:
        seq_length = sequence.get_playback_end()

    # create a new level to place actors
    success = new_world(new_level_path)
    print(f"new level: '{new_level_path}' created: {success}")
    assert success, RuntimeError('Failed to create level')

    level_visible_names, level_hidden_names = add_levels(persistent_level_path, new_level_path)
    level_visible_section, level_hidden_section = add_level_visibility_to_sequence(sequence, seq_length)

    # set level visibility
    level_visible_section.set_level_names(level_visible_names)
    level_hidden_section.set_level_names(level_hidden_names)

    # set created level as current level
    world = get_world()
    levels = get_levels(world)
    unreal.XF_BlueprintFunctionLibrary.set_level(world, levels[0])
    save_current_level()


def add_camera_to_sequence(
    sequence: unreal.LevelSequence,
    camera: unreal.CameraActor,
    camera_transform_keys: Optional[Union[SequenceTransformKey, List[SequenceTransformKey]]] = None,
    camera_fov: float = 90.0,
    seq_length: Optional[int] = None,
) -> unreal.CameraActor:
    if seq_length is None:
        seq_length = sequence.get_playback_end()

    # ------- add camera to seq ------ #
    camera_binding = sequence.add_possessable(camera)
    camera_track: unreal.MovieScene3DTransformTrack = camera_binding.add_track(unreal.MovieScene3DTransformTrack)  # type: ignore
    camera_section: unreal.MovieScene3DTransformSection = camera_track.add_section()  # type: ignore
    camera_section.set_start_frame(START_FRAME)
    camera_section.set_end_frame(seq_length)
    camera_component_binding = sequence.add_possessable(camera.camera_component)
    camera_component_binding.set_parent(camera_binding)

    # set the camera FOV
    fov_track, fov_section = add_property_float_track_to_binding(camera_component_binding, 'FieldOfView', camera_fov)

    # ------- add master track ------- #
    camera_cut_track: unreal.MovieSceneCameraCutTrack = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)  # type: ignore

    # add a camera cut track for this camera
    # make sure the camera cut is stretched to the START_FRAME mark
    camera_cut_section: unreal.MovieSceneCameraCutSection = camera_cut_track.add_section()  # type: ignore
    camera_cut_section.set_start_frame(START_FRAME)
    camera_cut_section.set_end_frame(seq_length)

    # set the camera cut to use this camera
    camera_cut_section.set_camera_binding_id(camera_binding.get_binding_id())

    # ------- add transform track ------- #
    transform_track, transform_section = add_or_find_transform_track_to_binding(camera_binding)
    if camera_transform_keys:
        # set the camera location and rotation
        add_transforms_to_binding(camera_binding, camera_transform_keys)

    return {
        'camera': {
            'binding': camera_binding,
            'self': camera,
        },
        'camera_component': {
            'binding': camera_component_binding,
            'self': camera.camera_component,
        },
        'fov': {'track': fov_track, 'section': fov_section},
        'transform': {'track': transform_track, 'section': transform_section},
    }


def add_spawnable_camera_to_sequence(
    sequence: unreal.LevelSequence,
    camera_name: str,
    camera_transform_keys: Optional[Union[SequenceTransformKey, List[SequenceTransformKey]]] = None,
    camera_class: Type[unreal.CameraActor] = unreal.CameraActor,
    camera_fov: float = 90.0,
    seq_length: Optional[int] = None,
) -> unreal.CameraActor:
    """Add a camera actor to the sequence.

    Args:
        sequence (unreal.LevelSequence): a loaded sequence.
        camera_name (str): name of the camera actor to set.
        camera_transform_keys (Optional[Union[SequenceTransformKey, List[SequenceTransformKey]]], optional): transform keys of the camera actor. Defaults to None.
        camera_class (Type[unreal.CameraActor], optional): the camera actor class to spawn. Defaults to unreal.CameraActor.
        camera_fov (float, optional): Filed of view of the camera. Defaults to 90.0.
        seq_length (Optional[int], optional): Sequence length. Defaults to None.

    Returns:
        unreal.CameraActor: _description_
    """
    # get sequence settings
    if seq_length is None:
        seq_length = sequence.get_playback_end()

    # ---------- add camera ---------- #
    # create a camera actor & add it to the sequence
    camera_binding = sequence.add_spawnable_from_class(camera_class)
    camera_actor: unreal.CameraActor = get_spawnable_actor_from_binding(sequence, camera_binding)
    camera_binding.set_name(camera_name)
    camera_actor.set_actor_label(camera_name)
    camera_component_binding = sequence.add_possessable(camera_actor.camera_component)
    camera_component_binding.set_parent(camera_binding)

    # set the camera FOV
    fov_track, fov_section = add_property_float_track_to_binding(camera_component_binding, 'FieldOfView', camera_fov)

    # ------- add master track ------- #
    # add master track (camera) to sequence
    # camera_cut_track = sequence.add_track(unreal.MovieSceneCameraCutTrack)
    camera_cut_track: unreal.MovieSceneCameraCutTrack = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)

    # add a camera cut track for this camera, make sure the camera cut is stretched to the START_FRAME mark
    camera_cut_section: unreal.MovieSceneCameraCutSection = camera_cut_track.add_section()
    camera_cut_section.set_start_frame(START_FRAME)
    camera_cut_section.set_end_frame(seq_length)

    # set the camera cut to use this camera

    # camera_binding_id = unreal.MovieSceneObjectBindingID()
    # camera_binding_id.set_editor_property("Guid", camera_binding.get_id())
    # camera_cut_section.set_editor_property("CameraBindingID", camera_binding_id)

    # camera_binding_id = sequence.make_binding_id(camera_binding, unreal.MovieSceneObjectBindingSpace.LOCAL)
    # camera_cut_section.set_camera_binding_id(camera_binding_id)

    camera_cut_section.set_camera_binding_id(camera_binding.get_binding_id())

    # ------- add transform track ------- #
    transform_track, transform_section = add_or_find_transform_track_to_binding(camera_binding)
    if camera_transform_keys:
        # set the camera location and rotation
        add_transforms_to_binding(camera_binding, camera_transform_keys)

    return {
        'camera': {
            'binding': camera_binding,
            'self': camera_actor,
        },
        'camera_component': {
            'binding': camera_component_binding,
            'self': camera_actor.camera_component,
        },
        'fov': {'track': fov_track, 'section': fov_section},
        'transform': {'track': transform_track, 'section': transform_section},
    }


def add_actor_to_sequence(
    sequence: unreal.LevelSequence,
    actor: unreal.Actor,
    actor_transform_keys: Optional[Union[SequenceTransformKey, List[SequenceTransformKey]]] = None,
    actor_stencil_value: int = 1,
    animation_asset: Optional[unreal.AnimSequence] = None,
    seq_fps: Optional[float] = None,
    seq_length: Optional[int] = None,
) -> Dict[str, Any]:
    # get sequence settings
    if seq_fps is None:
        seq_fps = get_sequence_fps(sequence)
    if seq_length is None:
        if animation_asset:
            seq_length = get_animation_length(animation_asset, seq_fps)
        else:
            seq_length = sequence.get_playback_end()

    # ------- add actor to seq ------ #
    actor_binding = sequence.add_possessable(actor)

    # mesh_component = actor.skeletal_mesh_component
    mesh_component = get_actor_mesh_component(actor)
    mesh_component_binding = sequence.add_possessable(mesh_component)

    # set stencil value
    custom_depth_track, custom_depth_section = add_property_bool_track_to_binding(
        mesh_component_binding, 'bRenderCustomDepth', True
    )
    stencil_value_track, stencil_value_section = add_property_int_track_to_binding(
        mesh_component_binding, 'CustomDepthStencilValue', actor_stencil_value
    )

    # add animation
    if animation_asset:
        add_animation_to_binding(actor_binding, animation_asset, seq_length, seq_fps)

    # ------- add transform track ------- #
    transform_track, transform_section = add_or_find_transform_track_to_binding(actor_binding)
    if actor_transform_keys:
        add_transforms_to_binding(actor_binding, actor_transform_keys)

    return {
        'actor': {'binding': actor_binding, 'self': actor},
        'transform': {'track': transform_track, 'section': transform_section},
        # "animation": {"track": animation_track, "section": animation_section},
        'mesh_component': {
            'binding': mesh_component_binding,
            'self': mesh_component,
            'custom_depth': {'track': custom_depth_track, 'section': custom_depth_section},
            'stencil_value': {'track': stencil_value_track, 'section': stencil_value_section},
        },
    }


def add_spawnable_actor_to_sequence(
    sequence: unreal.LevelSequence,
    actor_name: str,
    actor_asset: Union[unreal.SkeletalMesh, unreal.StaticMesh],
    animation_asset: Optional[unreal.AnimSequence] = None,
    actor_transform_keys: Optional[Union[SequenceTransformKey, List[SequenceTransformKey]]] = None,
    actor_stencil_value: int = 1,
    seq_fps: Optional[float] = None,
    seq_length: Optional[int] = None,
) -> Dict[str, Any]:
    # get sequence settings
    if seq_fps is None:
        seq_fps = get_sequence_fps(sequence)
    if seq_length is None:
        if animation_asset:
            seq_length = get_animation_length(animation_asset, seq_fps)
        else:
            seq_length = sequence.get_playback_end()

    # add actor to sequence
    actor_binding = sequence.add_spawnable_from_instance(actor_asset)
    actor = get_spawnable_actor_from_binding(sequence, actor_binding)
    actor_binding.set_name(actor_name)
    actor.set_actor_label(actor_name)

    # mesh_component = actor.skeletal_mesh_component
    mesh_component = get_actor_mesh_component(actor)
    mesh_component_binding = sequence.add_possessable(mesh_component)

    # set stencil value
    custom_depth_track, custom_depth_section = add_property_bool_track_to_binding(
        mesh_component_binding, 'bRenderCustomDepth', True
    )
    stencil_value_track, stencil_value_section = add_property_int_track_to_binding(
        mesh_component_binding, 'CustomDepthStencilValue', actor_stencil_value
    )

    # add animation
    if animation_asset:
        add_animation_to_binding(actor_binding, animation_asset, seq_length, seq_fps)

    # ------- add transform track ------- #
    transform_track, transform_section = add_or_find_transform_track_to_binding(actor_binding)
    if actor_transform_keys:
        add_transforms_to_binding(actor_binding, actor_transform_keys)

    return {
        'actor': {'binding': actor_binding, 'self': actor},
        'transform': {'track': transform_track, 'section': transform_section},
        # "animation": {"track": animation_track, "section": animation_section},
        'mesh_component': {
            'binding': mesh_component_binding,
            'self': mesh_component,
            'custom_depth': {'track': custom_depth_track, 'section': custom_depth_section},
            'stencil_value': {'track': stencil_value_track, 'section': stencil_value_section},
        },
    }


def generate_sequence(
    sequence_dir: str,
    sequence_name: str,
    seq_fps: Optional[float] = None,
    seq_length: Optional[int] = None,
) -> unreal.LevelSequence:
    asset_tools: unreal.AssetTools = unreal.AssetToolsHelpers.get_asset_tools()  # type: ignore
    new_sequence: unreal.LevelSequence = asset_tools.create_asset(
        sequence_name,
        sequence_dir,
        unreal.LevelSequence,
        unreal.LevelSequenceFactoryNew(),
    )
    assert new_sequence is not None, f'Failed to create LevelSequence: {sequence_dir}/{sequence_name}'
    # Set sequence config
    if seq_fps:
        new_sequence.set_display_rate(unreal.FrameRate(seq_fps))
    if seq_length:
        new_sequence.set_playback_end(seq_length)
    return new_sequence


class Sequence:
    map_path = None
    sequence_path = None
    sequence_data_asset: unreal.DataAsset = None  # contains sequence_path and map_path
    sequence: unreal.LevelSequence = None
    bindings: Dict[str, Dict[str, Any]] = {}

    def __init__(self) -> NoReturn:
        raise Exception('Sequence (XRFeitoriaUnreal/Python) should not be instantiated')

    def __del__(self) -> NoReturn:
        # TODO: when error was raised from spawn_xxx, the sequence is not closed, which would cause unable to delete the sequence asset
        del self.map_path
        del self.sequence_path
        del self.sequence
        del self.sequence_data_asset
        del self.bindings

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
        seq_path: str,
    ) -> None:
        assert unreal.EditorAssetLibrary.does_asset_exist(map_path), f'Map `{map_path}` does not exist'
        assert unreal.EditorAssetLibrary.does_asset_exist(
            seq_path,
        ), f'Sequence `{seq_path}` does not exist'

        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        cls.map_path = map_path
        cls.sequence_path = seq_path
        cls.sequence: unreal.LevelSequence = unreal.load_asset(cls.sequence_path)

    @classmethod
    def new(
        cls,
        seq_name: str,
        map_path: 'Optional[str]' = None,
        seq_dir: 'Optional[str]' = None,
        seq_fps: 'Optional[float]' = None,
        seq_length: 'Optional[int]' = None,
        replace: bool = False,
    ) -> str:
        """Create a new sequence.

        Args:
            seq_name (str): name of the sequence.
            map_path (Optional[str], optional): path of the map asset. Defaults to None. When None, the current map will be used.
            seq_dir (Optional[str], optional): path of the sequence asset. Defaults to None.
            seq_fps (Optional[float], optional): FPS of the sequence. Defaults to None.
            seq_length (Optional[int], optional): length of the sequence. Defaults to None.
            replace (bool, optional): whether to replace the sequence if it already exists. Defaults to False.

        Returns:
            str: path of the data asset of sequence data, containing sequence_path and map_path.
        """
        if map_path is None:
            map_path = EditorLevelSub.get_current_level().get_path_name().split('.')[0]
        assert unreal.EditorAssetLibrary.does_asset_exist(map_path), f'Map `{map_path}` does not exist'
        if seq_dir is None:
            seq_dir = DEFAULT_SEQUENCE_PATH

        data_asset_path = f'{seq_dir}/{seq_name}{data_asset_suffix}'
        if unreal.EditorAssetLibrary.does_asset_exist(f'{seq_dir}/{seq_name}'):
            if replace:
                unreal.EditorAssetLibrary.delete_asset(f'{seq_dir}/{seq_name}')
                unreal.EditorAssetLibrary.delete_asset(data_asset_path)
            else:
                raise Exception(f'Sequence `{seq_dir}/{seq_name}` already exists, use `replace=True` to replace it')

        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        cls.map_path = map_path
        cls.sequence = generate_sequence(
            sequence_dir=seq_dir,
            sequence_name=seq_name,
            seq_fps=seq_fps,
            seq_length=seq_length,
        )
        cls.sequence_path = f'{seq_dir}/{seq_name}'

        cls.sequence_data_asset = cls.new_data_asset(
            asset_path=data_asset_path,
            map_path=cls.map_path,
            sequence_path=cls.sequence_path,
        )
        return data_asset_path

    @classmethod
    def show(cls) -> None:
        assert cls.sequence is not None, 'Sequence not initialized'
        unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(cls.sequence)

    @staticmethod
    def new_data_asset(
        asset_path: str,
        sequence_path: str,
        map_path: str,
    ) -> unreal.DataAsset:
        """Create a new data asset of sequence data.

        Args:
            asset_path (str): path of the data asset.
            sequence_path (str): path of the sequence asset.
            map_path (str): path of the map asset.

        Returns:
            unreal.DataAsset: the created data asset.

        Notes:
            SequenceData Properties:
                - "SequencePath": str
                - "MapPath": str
        """
        # maybe `unreal.EditorAssetLibrary.load_blueprint_class`
        unreal.EditorAssetLibrary.duplicate_asset(
            source_asset_path=DEFAULT_SEQUENCE_DATA_ASSET,
            destination_asset_path=asset_path,
        )
        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            raise RuntimeError(f'Failed to create data asset: {asset_path}')
        asset = unreal.load_asset(asset_path)
        assert asset is not None, f'Failed to create data asset: {asset_path}'
        asset.set_editor_property('SequencePath', get_soft_object_path(sequence_path))
        asset.set_editor_property('MapPath', get_soft_object_path(map_path))
        unreal.EditorAssetLibrary.save_asset(asset_path)
        return asset

    @staticmethod
    def get_data_asset_info(data_asset_path: str) -> Tuple[str, str]:
        """Get sequence path and map path from data asset.

        Args:
            data_asset_path (str): path of the data asset.
        """
        seq_data_asset = unreal.load_asset(data_asset_path)
        assert seq_data_asset is not None, f'Failed to load data asset: {data_asset_path}'
        seq_path = seq_data_asset.get_editor_property('SequencePath').export_text()
        map_path = seq_data_asset.get_editor_property('MapPath').export_text()
        return seq_path.split('.')[0], map_path.split('.')[0]

    # ------ add actor and camera -------- #

    @classmethod
    def add_camera(
        cls,
        camera_name: str,
        transform_keys: 'Optional[TransformKeys]' = None,
        fov: float = 90.0,
        spawnable: bool = False,
    ):
        """Spawn a camera in sequence.

        Args:
            transform_keys (Optional[TransformKeys], optional): List of transform keys. Defaults to None.
            fov (float, optional): Field of view of camera. Defaults to 90.0.
            camera_name (str, optional): Name of camera to set in sequence. Defaults to "Camera".
        """
        assert cls.sequence is not None, 'Sequence not initialized'
        if spawnable:
            bindings = add_spawnable_camera_to_sequence(
                sequence=cls.sequence,
                camera_name=camera_name,
                camera_transform_keys=transform_keys,
                camera_fov=fov,
            )
            cls.bindings[camera_name] = bindings
        else:
            camera = utils_actor.get_actor_by_name(camera_name)
            bindings = add_camera_to_sequence(
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
        actor: 'Optional[Union[str, unreal.Actor]]' = None,
        transform_keys: 'Optional[TransformKeys]' = None,
        stencil_value: int = 1,
        animation_asset: 'Optional[Union[str, unreal.AnimSequence]]' = None,
    ) -> None:
        """Spawn an actor in sequence.

        Args:
            actor (Union[str, unreal.Actor]): actor path (e.g. '/Game/Cube') / loaded asset (via `unreal.load_asset('/Game/Cube')`)
            animation_asset (Union[str, unreal.AnimSequence]): animation path (e.g. '/Game/Anim') / loaded asset (via `unreal.load_asset('/Game/Anim')`). Can be None which means no animation.
            actor_name (str, optional): Name of actor to set in sequence. Defaults to "Actor".
            transform_keys (TransformKeys, optional): List of transform keys. Defaults to None.
            actor_stencil_value (int, optional): Stencil value of actor, used for specifying the mask color for this actor (mask id). Defaults to 1.
        """
        assert cls.sequence is not None, 'Sequence not initialized'
        if animation_asset and isinstance(animation_asset, str):
            animation_asset = unreal.load_asset(animation_asset)
        if isinstance(actor, str):
            actor = unreal.load_asset(actor)

        if actor:
            bindings = add_spawnable_actor_to_sequence(
                sequence=cls.sequence,
                actor_name=actor_name,
                actor_asset=actor,
                animation_asset=animation_asset,
                actor_transform_keys=transform_keys,
                actor_stencil_value=stencil_value,
            )
            cls.bindings[actor_name] = bindings

        else:
            actor = utils_actor.get_actor_by_name(actor_name)
            bindings = add_actor_to_sequence(
                sequence=cls.sequence,
                actor=actor,
                actor_transform_keys=transform_keys,
                actor_stencil_value=stencil_value,
                animation_asset=animation_asset,
            )
            cls.bindings[actor_name] = bindings


if __name__ == '__main__':
    Sequence.new('/Game/NewMap', 'test1')
    Sequence.spawn_camera(transform_keys=SequenceTransformKey(frame=0, location=(0, 0, 0), rotation=(0, 0, 0)))
    Sequence.spawn_actor(
        '/Game/StarterContent/Props/SM_Chair',
        transform_keys=SequenceTransformKey(frame=0, location=(0, 0, 0), rotation=(0, 0, 0)),
    )
