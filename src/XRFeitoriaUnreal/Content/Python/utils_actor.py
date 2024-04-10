from typing import Dict, List, Tuple, Union

import unreal
from constants import SubSystem, mask_colors
from utils import get_world


def get_stencil_value(actor: unreal.Actor) -> int:
    # skeletal mesh component
    for skeletal_mesh_component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        stencil_value = skeletal_mesh_component.get_editor_property('custom_depth_stencil_value')
        return stencil_value
    # static mesh component
    for static_mesh_component in actor.get_components_by_class(unreal.StaticMeshComponent):
        stencil_value = static_mesh_component.get_editor_property('custom_depth_stencil_value')
        return stencil_value


def set_stencil_value(actor: unreal.Actor, stencil_value: int, receives_decals: bool = False) -> None:
    # skeletal mesh component
    for skeletal_mesh_component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        skeletal_mesh_component.set_render_custom_depth(True)
        skeletal_mesh_component.set_custom_depth_stencil_value(stencil_value)
        skeletal_mesh_component.set_editor_property('receives_decals', receives_decals)
    # static mesh component
    for static_mesh_component in actor.get_components_by_class(unreal.StaticMeshComponent):
        static_mesh_component.set_render_custom_depth(True)
        static_mesh_component.set_custom_depth_stencil_value(stencil_value)
        static_mesh_component.set_editor_property('receives_decals', receives_decals)


def get_mask_color(stencil_value: int) -> Tuple[int, int, int]:
    return mask_colors[stencil_value]['rgb']


def get_actor_mask_color(actor: unreal.Actor) -> Tuple[int, int, int]:
    stencil_value = get_stencil_value(actor)
    return get_mask_color(stencil_value)


def get_actor_mesh_component(
    actor: Union[unreal.SkeletalMeshActor, unreal.StaticMeshActor]
) -> Union[unreal.SkeletalMeshComponent, unreal.StaticMeshComponent]:
    if isinstance(actor, unreal.SkeletalMeshActor):
        mesh_component = actor.skeletal_mesh_component
    elif isinstance(actor, unreal.StaticMeshActor):
        mesh_component = actor.static_mesh_component
    else:
        raise TypeError(f'{actor.get_name()} is not a SkeletalMeshActor or StaticMeshActor')
    return mesh_component


def get_skeleton_names(actor_asset_path: str) -> List[str]:
    """Retrieves the names of the bones in the skeleton of a SkeletalMeshActor (also can
    be child class of it).

    Args:
        actor_asset_path (str): The asset path of the SkeletalMeshActor.

    Returns:
        List[str]: A set of bone names in the skeleton.

    Raises:
        AssertionError: If the spawned actor is not a SkeletalMeshActor.
    """
    actor = spawn_actor_from_object(unreal.load_asset(actor_asset_path))
    try:
        assert isinstance(actor, unreal.SkeletalMeshActor), f'{actor.get_name()} is not a SkeletalMeshActor'
        skeletal_mesh = actor.skeletal_mesh_component.skeletal_mesh
        bone_names = [str(bone_name) for bone_name in skeletal_mesh.skeleton.get_reference_pose().get_bone_names()]
        curve_names = [morph.get_name() for morph in skeletal_mesh.morph_targets]
        skeleton_names = bone_names + curve_names
    except Exception as e:
        unreal.log_warning(f'Error: {e}')
        skeleton_names = []
    finally:
        destroy_actor(actor)
    return skeleton_names


def get_z_by_raycast(x: float, y: float, debug: bool = False):
    z_infinity_positive = 100000
    z_infinity_negative = -100000
    start = unreal.Vector(x, y, z_infinity_positive)
    end = unreal.Vector(x, y, z_infinity_negative)
    trace_channel = unreal.TraceTypeQuery.TRACE_TYPE_QUERY2
    actors_to_ignore = unreal.Array(unreal.Actor)

    object_types = unreal.Array(unreal.ObjectTypeQuery)
    _object_types = [
        unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1,
        unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2,
        unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY3,
        unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY4,
        unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY5,
        unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY6,
    ]
    object_types.extend(_object_types)

    if debug:
        DrawDebugTrace = unreal.DrawDebugTrace.FOR_DURATION
    else:
        DrawDebugTrace = unreal.DrawDebugTrace.NONE

    hits = unreal.SystemLibrary.line_trace_multi_for_objects(
        get_world(),
        start,
        end,
        object_types=object_types,
        trace_complex=True,
        actors_to_ignore=actors_to_ignore,
        draw_debug_type=DrawDebugTrace,
        ignore_self=False,
        trace_color=unreal.LinearColor(r=1, g=0, b=0, a=1),
        trace_hit_color=unreal.LinearColor(r=0, g=0, b=1, a=1),
        draw_time=60,
    )

    return hits


def hit_to_z(hit) -> float:
    z = hit.to_tuple()[4].z
    return z


def draw_actor_bbox(
    actor: unreal.Actor,
    color: unreal.LinearColor = unreal.LinearColor(1, 0, 0, 1),
    duration: int = 10,
    thickness: int = 1,
) -> None:
    bbox: Tuple[unreal.Vector, unreal.Vector] = actor.get_actor_bounds(False, include_from_child_actors=True)
    world = get_world()

    actor_name = actor.get_fname()
    print(f'{actor_name} center: {bbox[0].to_tuple()}')
    print(f'{actor_name} extend: {bbox[1].to_tuple()}')

    unreal.SystemLibrary.draw_debug_box(world, bbox[0], bbox[1], color, duration=duration, thickness=thickness)


def draw_selected_actors_bbox(
    color: unreal.LinearColor = unreal.LinearColor(1, 0, 0, 1), duration: int = 10, thickness: int = 1
) -> None:
    actors = get_selected_actors()
    for actor in actors:
        draw_actor_bbox(actor, color, duration, thickness)


def spawn_actor_from_object(
    actor_object: unreal.Object,
    location: Tuple[float, float, float] = (0, 0, 0),
    rotation: Tuple[float, float, float] = (0, 0, 0),
    scale: Tuple[float, float, float] = (1, 1, 1),
) -> unreal.Actor:
    """Spawn an actor from an object.

    Args:
        actor_object (unreal.Object): Actor loaded from ``unreal.load_asset(path)``
        location (Tuple[float, float, float]): Location of the actor. Units in meters. Defaults to (0, 0, 0).
        rotation (Tuple[float, float, float], optional): Rotation of the actor. Units in degrees. Defaults to (0, 0, 0).
        scale (Tuple[float, float, float], optional): Scale of the actor. Defaults to (1, 1, 1).

    Returns:
        unreal.Actor: Spawned actor

    Examples:
        >>> import unreal
        >>> import utils_actor
        >>> actor_object = unreal.load_asset('/Engine/BasicShapes/Cube')
        >>> actor = utils_actor.spawn_actor_from_object(actor_object, location=(1, 1, 1))
    """
    location = unreal.Vector(location[0], location[1], location[2])
    rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2])
    scale = unreal.Vector(scale[0], scale[1], scale[2])
    # convert from meters to centimeters
    location *= 100.0

    if SubSystem.EditorActorSub:
        actor = SubSystem.EditorActorSub.spawn_actor_from_object(
            object_to_use=actor_object, location=location, rotation=rotation
        )
    else:
        actor = unreal.EditorLevelLibrary().spawn_actor_from_object(
            actor_class=actor_object, location=location, rotation=rotation
        )
    actor.set_actor_scale3d(scale)
    return actor


def spawn_actor_from_class(
    actor_class: unreal.Actor,
    location: Tuple[float, float, float] = (0, 0, 0),
    rotation: Tuple[float, float, float] = (0, 0, 0),
    scale: Tuple[float, float, float] = (1, 1, 1),
) -> unreal.Actor:
    location = unreal.Vector(location[0], location[1], location[2])
    rotation = unreal.Rotator(rotation[0], rotation[1], rotation[2])
    scale = unreal.Vector(scale[0], scale[1], scale[2])
    # convert from meters to centimeters
    location *= 100.00

    if SubSystem.EditorActorSub:
        actor = SubSystem.EditorActorSub.spawn_actor_from_class(
            actor_class=actor_class, location=location, rotation=rotation
        )
    else:
        actor = unreal.EditorLevelLibrary().spawn_actor_from_class(
            actor_class=actor_class, location=location, rotation=rotation
        )
    actor.set_actor_scale3d(scale)
    return actor


def get_actor_by_name(actor_name: str) -> unreal.Actor:
    actors = get_all_actors_dict()
    if actor_name not in actors:
        raise Exception(f"Actor '{actor_name}' not found")
    return actors[actor_name]


def get_all_actors_name() -> List[str]:
    actors = get_all_actors_dict()
    return list(actors.keys())


def get_all_actors_dict() -> Dict[str, unreal.Actor]:
    actors = {}
    for actor in get_all_actors():
        if actor.get_actor_label() in actors:
            raise Exception(f'Multiple Actors named {actor.get_actor_label()}')
        actors[actor.get_actor_label()] = actor
    return actors


def get_selected_actors():
    # ! Selected
    if SubSystem.EditorActorSub:
        selected_actors = SubSystem.EditorActorSub.get_selected_level_actors()
    else:
        selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()
    return selected_actors


def get_class_actor(actor_class) -> unreal.Actor:
    # ! Class
    world = get_world()
    class_actor = unreal.GameplayStatics.get_actor_of_class(world, actor_class)
    return class_actor


def get_class_actors(actor_class) -> List[unreal.Actor]:
    # ! Class
    world = get_world()
    class_actors = unreal.GameplayStatics.get_all_actors_of_class(world, actor_class)
    return class_actors


def get_tag_actors(actor_tag) -> List[unreal.Actor]:
    # ! Tag
    world = get_world()
    tag_actors = unreal.GameplayStatics.get_all_actors_with_tag(world, actor_tag)
    return tag_actors


def get_all_actors() -> List[unreal.Actor]:
    # ! All
    world = get_world()
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    return all_actors


def get_components_of_class(actor, component_class) -> List:
    # ! Component
    components = actor.get_components_by_class(component_class)
    return components


def destroy_actor(actor: unreal.Actor):
    if SubSystem.EditorActorSub:
        SubSystem.EditorActorSub.destroy_actor(actor)
    else:
        unreal.EditorLevelLibrary().destroy_actor(actor)
