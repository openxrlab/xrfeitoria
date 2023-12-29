import bpy

from .constants import default_level_blender
from .core.factory import XRFeitoriaBlenderFactory


class LevelCameras(bpy.types.PropertyGroup):
    # name: bpy.props.StringProperty()
    camera: bpy.props.PointerProperty(type=bpy.types.Object)
    location: bpy.props.FloatVectorProperty(size=3)
    rotation: bpy.props.FloatVectorProperty(size=3)
    scale: bpy.props.FloatVectorProperty(size=3)
    level_fov: bpy.props.FloatProperty()
    sequence_fov: bpy.props.FloatProperty()
    sequence_animation: bpy.props.PointerProperty(type=bpy.types.Action)


class LevelActors(bpy.types.PropertyGroup):
    actor: bpy.props.PointerProperty(type=bpy.types.Object)
    location: bpy.props.FloatVectorProperty(size=3)
    rotation: bpy.props.FloatVectorProperty(size=3)
    scale: bpy.props.FloatVectorProperty(size=3)
    level_animation: bpy.props.PointerProperty(type=bpy.types.Action)
    level_stencil_value: bpy.props.IntProperty()
    sequence_animation: bpy.props.PointerProperty(type=bpy.types.Action)
    sequence_stencil_value: bpy.props.IntProperty()


## sequence properties for collection
class SequenceProperties(bpy.types.PropertyGroup):
    level: bpy.props.PointerProperty(type=bpy.types.Scene)
    level_cameras: bpy.props.CollectionProperty(type=LevelCameras)
    level_actors: bpy.props.CollectionProperty(type=LevelActors)
    fps: bpy.props.IntProperty()
    frame_start: bpy.props.IntProperty()
    frame_end: bpy.props.IntProperty()
    frame_current: bpy.props.IntProperty()
    resolution_x: bpy.props.IntProperty()
    resolution_y: bpy.props.IntProperty()


## level properties for scene
class LevelProperties(bpy.types.PropertyGroup):
    def active_sequence_update(self, context):
        """Open or close sequence when self.active_sequence is changed."""
        if self.active_sequence is None:
            XRFeitoriaBlenderFactory.close_sequence()
        elif XRFeitoriaBlenderFactory.is_sequence_collecion(self.active_sequence):
            level_scene, _, _, _, _, _, _ = XRFeitoriaBlenderFactory.get_sequence_properties(
                collection=self.active_sequence
            )
            if self.active_sequence.name not in level_scene.collection.children:
                XRFeitoriaBlenderFactory.open_sequence(self.active_sequence.name)
        else:
            pass

    def filter_sequence_collection(self, collection) -> bool:
        """Only sequence collection can be set as active sequence.

        Args:
            collection (bpy.types.Collection): Collection.

        Returns:
            bool: True if the collection is a sequence collection and in the active scene.
        """
        return (
            XRFeitoriaBlenderFactory.is_sequence_collecion(collection)
            and collection.sequence_properties.level == bpy.context.scene
        )

    active_sequence: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        update=active_sequence_update,
        name='Active Sequence',
        poll=filter_sequence_collection,
    )


property_classes = [
    LevelCameras,
    LevelActors,
    LevelProperties,
    SequenceProperties,
]


def register():
    for property_class in property_classes:
        bpy.utils.register_class(property_class)

    bpy.types.Scene.default_level_blender = bpy.props.StringProperty(
        name='Default Level Blender', default=default_level_blender
    )
    bpy.types.Scene.level_properties = bpy.props.PointerProperty(type=LevelProperties)
    bpy.types.Collection.sequence_properties = bpy.props.PointerProperty(type=SequenceProperties)


def unregister():
    for property_class in property_classes:
        bpy.utils.unregister_class(property_class)

    del bpy.types.Scene.default_level_blender
    del bpy.types.Scene.level_properties
    del bpy.types.Collection.sequence_properties
