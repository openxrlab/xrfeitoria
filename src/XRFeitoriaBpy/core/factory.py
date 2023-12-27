import json
import math
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import bpy
import numpy as np

from .. import logger
from ..constants import Tuple3


class XRFeitoriaBlenderFactory:
    #####################################
    ######## Scene & Collection #########
    #####################################

    # --------- NEW  -----------
    def new_collection(name: str, replace: bool = False) -> 'bpy.types.Collection':
        """Create a new collection.

        Args:
            name (str): Name of the new collection.
            replace (bool, optional): Replace the exist same-name collection. Defaults to False.

        Raises:
            ValueError: If the collection already exists and 'repalce=False'.

        Returns:
            bpy.types.Collection: New collection.
        """
        if replace:
            XRFeitoriaBlenderFactory.delete_sequence(name)
        if name in bpy.data.collections:
            raise ValueError(f"Collection '{name}' already exists.")
        collection = bpy.data.collections.new(name)
        collection.use_fake_user = True
        return collection

    def new_scene(name: str, replace: bool = False) -> 'bpy.types.Scene':
        """Create a new scene.

        Args:
            name (str): Name of the new scene.
            replace (bool, optional): Replace the exist same-name scene. Defaults to False.

        Raises:
            ValueError:  If the scene already exists and 'replace=False'.

        Returns:
            bpy.types.Scene: New scene.
        """
        if replace:
            XRFeitoriaBlenderFactory.delete_sequence(name)
        if name in bpy.data.scenes:
            raise ValueError(f"Scene '{name}' already exists.")
        scene = bpy.data.scenes.new(name)
        return scene

    # --------- GET  -----------
    def get_collection(name: str) -> 'bpy.types.Collection':
        """Get a collection by name.

        Args:
            name (str): Name of the collection.

        Raises:
            ValueError: If the collection does not exists.

        Returns:
            bpy.types.Collection: The collection.
        """
        if name not in bpy.data.collections:
            raise ValueError(f"Collection '{name}' does not exists in this blend file.")
        return bpy.data.collections[name]

    def get_scene(name: str) -> 'bpy.types.Scene':
        """Get a scene by name.

        Args:
            name (str): Name of the scene.

        Raises:
            ValueError: If the scene does not exists.

        Returns:
            bpy.types.Scene: The scene.
        """
        if name not in bpy.data.scenes:
            raise ValueError(f"Scene '{name}' does not exists in this blend file.")
        return bpy.data.scenes[name]

    def get_active_collection(scene: 'bpy.types.Scene' = None) -> 'bpy.types.Collection':
        """Get the active collection.

        Returns:
            bpy.types.Collection: Active collection.
        """
        scene = XRFeitoriaBlenderFactory.get_active_scene() if not scene else scene
        sequence_collection = scene.level_properties.active_sequence
        if sequence_collection:
            return sequence_collection
        elif scene.name in scene.collection.children.keys():
            level_collection = XRFeitoriaBlenderFactory.get_collection(scene.name)
            return level_collection
        else:
            return scene.collection

    def set_level_properties(scene: 'bpy.types.Scene', active_seq: 'bpy.types.Collection') -> None:
        """Set the active sequence.

        Args:
            scene (bpy.types.Scene): Scene.
            active_seq (bpy.types.Collection): Collection of the active sequence.
        """
        scene.level_properties.active_sequence = active_seq

    def set_sequence_properties(
        collection: 'bpy.types.Collection',
        level: 'bpy.types.Scene',
        fps: int,
        frame_start: int,
        frame_end: int,
        frame_current: int,
    ) -> None:
        """Set the sequence properties.

        Args:
            collection (bpy.types.Collection): Collection of the sequence.
            level (bpy.types.Scene): Level(scene) of the sequence.
            fps (int): FPS of the sequence.
            frame_start (int): Start frame of the sequence.
            frame_end (int): End frame of the sequence.
            frame_current (int): Current frame of the sequence.
        """
        collection.sequence_properties.level = level
        collection.sequence_properties.fps = fps
        collection.sequence_properties.frame_start = frame_start
        collection.sequence_properties.frame_end = frame_end
        collection.sequence_properties.frame_current = frame_current

    def get_sequence_properties(collection: 'bpy.types.Collection') -> 'Tuple[bpy.types.Scene, int, int, int, int]':
        """Get the sequence properties.

        Args:
            collection (bpy.types.Collection): Collection of the sequence.

        Returns:
            Tuple[bpy.types.Scene, int, int, int, int]:
                The level(scene), FPS of the sequence, Start frame of the sequence, End frame of the sequence, Current frame of the sequence.
        """
        level = collection.sequence_properties.level
        fps = collection.sequence_properties.fps
        frame_start = collection.sequence_properties.frame_start
        frame_end = collection.sequence_properties.frame_end
        frame_current = collection.sequence_properties.frame_current
        return level, fps, frame_start, frame_end, frame_current

    def open_sequence(seq_name: str) -> 'bpy.types.Scene':
        """Open the given sequence.

        Args:
            seq_name (str): Name of the sequence.
        """
        # get sequence collection
        seq_collection = XRFeitoriaBlenderFactory.get_collection(seq_name)
        # get sequence properties
        level_scene, fps, frame_start, frame_end, frame_current = XRFeitoriaBlenderFactory.get_sequence_properties(
            collection=seq_collection
        )
        # deactivate all cameras in this level
        for obj in level_scene.objects:
            if obj.type == 'CAMERA':
                XRFeitoriaBlenderFactory.set_camera_activity(camera_name=obj.name, scene=level_scene, active=False)

        # clear all sequences in this level
        for collection in level_scene.collection.children:
            if XRFeitoriaBlenderFactory.is_sequence_collecion(collection):
                XRFeitoriaBlenderFactory.unlink_collection_from_scene(collection=collection, scene=level_scene)

        # link sequence(seq_collection) to level(level_scene)
        XRFeitoriaBlenderFactory.link_collection_to_scene(collection=seq_collection, scene=level_scene)

        # assign sequence properties to level scene
        level_scene.frame_start = frame_start
        level_scene.frame_end = frame_end
        level_scene.frame_current = frame_current
        level_scene.render.fps = fps

        # set cameras in this sequence to active
        for obj in seq_collection.objects:
            if obj.type == 'CAMERA':
                XRFeitoriaBlenderFactory.set_camera_activity(camera_name=obj.name, scene=level_scene, active=True)

        # set level cameras been used in this sequence to active
        for camera_data in seq_collection.sequence_properties.level_cameras:
            camera = camera_data.camera
            XRFeitoriaBlenderFactory.set_camera_activity(camera_name=camera.name, scene=level_scene, active=True)
            camera.data.angle = camera_data.sequence_fov
            if camera_data.sequence_animation:
                XRFeitoriaBlenderFactory.apply_action_to_actor(action=camera_data.sequence_animation, actor=camera)

        # set level actors' properties
        for actor_data in seq_collection.sequence_properties.level_actors:
            actor = actor_data.actor
            actor.pass_index = actor_data.sequence_stencil_value
            for child in actor.children:
                child.pass_index = actor_data.sequence_stencil_value
            if actor_data.sequence_animation:
                XRFeitoriaBlenderFactory.apply_action_to_actor(action=actor_data.sequence_animation, actor=actor)

        # set scene to active
        XRFeitoriaBlenderFactory.set_scene_active(level_scene)
        # set collection to active
        XRFeitoriaBlenderFactory.set_collection_active(seq_collection)

        return level_scene

    def close_sequence() -> None:
        """Close the active sequence."""
        level_scene = XRFeitoriaBlenderFactory.get_active_scene()

        # deactivate all cameras in this level
        for obj in level_scene.objects:
            if obj.type == 'CAMERA':
                XRFeitoriaBlenderFactory.set_camera_activity(camera_name=obj.name, scene=level_scene, active=False)

        # clear all sequences in this level
        for collection in level_scene.collection.children:
            if XRFeitoriaBlenderFactory.is_sequence_collecion(collection):
                # save sequence properties
                XRFeitoriaBlenderFactory.set_sequence_properties(
                    collection=collection,
                    level=level_scene,
                    fps=level_scene.render.fps,
                    frame_start=level_scene.frame_start,
                    frame_end=level_scene.frame_end,
                    frame_current=level_scene.frame_current
                )
                # unlink the sequence from the level
                XRFeitoriaBlenderFactory.unlink_collection_from_scene(collection=collection, scene=level_scene)
                # restore level actors' properties
                for actor_data in collection.sequence_properties.level_actors:
                    actor = actor_data.actor
                    actor.pass_index = actor_data.level_stencil_value
                    for child in actor.children:
                        child.pass_index = actor_data.level_stencil_value
                    if actor_data.level_animation:
                        XRFeitoriaBlenderFactory.apply_action_to_actor(action=actor_data.level_animation, actor=actor)
                    else:
                        actor.animation_data_clear()
                    actor.location = actor_data.location
                    actor.rotation_euler = actor_data.rotation
                    actor.scale = actor_data.scale
                # restore level cameras' properties
                for camera_data in collection.sequence_properties.level_cameras:
                    camera = camera_data.camera
                    camera.animation_data_clear()
                    camera.data.angle = camera_data.level_fov
                    camera.location = camera_data.location
                    camera.rotation_euler = camera_data.rotation
                    camera.scale = camera_data.scale

    def tag_sequence_collection(collection: 'bpy.types.Collection') -> None:
        """Tag the given collection as the sequence collection.

        Args:
            collection (bpy.types.Collection): Collection to be tag as the sequence collection.
        """
        collection.color_tag = 'COLOR_01'

    def is_sequence_collecion(collection: 'bpy.types.Collection') -> bool:
        """Check if the given collection is a sequence collection.

        Args:
            collection (bpy.types.Collection): Collection to be checked.

        Returns:
            bool: True if the collection is a sequence collection, else False.
        """
        if collection.color_tag == 'COLOR_01':
            return True
        else:
            return False

    def get_active_scene() -> 'bpy.types.Scene':
        """Get the active scene.

        Returns:
            bpy.types.Scene: The active scene.
        """
        return bpy.context.scene

    def get_keys_range(scene: 'bpy.types.Scene') -> 'Tuple[int, int]':
        """Get the max keyframe range of all the objects in the given scene.

        Args:
            scene (bpy.types.Scene): The scene to get the max keyframe range.

        Returns:
            Tuple[int, int]: Max keyframe range.
        """
        key_start = 1e9
        key_end = 0
        for obj in scene.objects:
            key_start = min(key_start, XRFeitoriaBlenderFactory.get_obj_keys_range(obj)[0])
            key_end = max(key_end, XRFeitoriaBlenderFactory.get_obj_keys_range(obj)[1])
        if key_start > key_end:
            key_start, key_end = 0, 0
        return int(key_start), int(key_end)

    def get_obj_keys_range(obj: 'bpy.types.Object') -> 'Tuple[int, int]':
        """Get the keyframe range of the given object.

        Args:
            obj (bpy.types.Object): The object to get the keyframe range.

        Returns:
            Tuple[int, int]: Keyframe range of the object.
        """
        key_start = 1e9
        key_end = 0

        if obj.animation_data and obj.animation_data.action:
            key_start = min(key_start, obj.animation_data.action.fcurves[0].range()[0])
            key_end = max(key_end, obj.animation_data.action.fcurves[0].range()[1])
        elif obj.type == 'Armature' and obj.data.animation_data and obj.data.animation_data.action:
            key_start = min(key_start, obj.data.animation_data.action.fcurves[0].range()[0])
            key_end = max(key_end, obj.data.animation_data.action.fcurves[0].range()[1])

        if key_start > key_end:
            key_start, key_end = 0, 0

        return int(key_start), int(key_end)

    def get_frame_range(scene: 'bpy.types.Scene') -> Tuple[int, int]:
        """Get the frame range of the given scene.

        Args:
            scene (bpy.types.Scene): The scene to get the frame range.

        Returns:
            Tuple[int, int]: Frame range of the scene.
        """
        return scene.frame_start, scene.frame_end

    def get_scene_and_collection_for_new_object(
        collection_name: str = None,
    ) -> Tuple['bpy.types.Scene', 'bpy.types.Collection']:
        """Get scene and collection for adding new object by given 'collection_name'.

        Returns:
            Tuple['bpy.types.Scene', 'bpy.types.Collection']: Scene and collection for adding new object
        """
        # get scene
        scene = XRFeitoriaBlenderFactory.get_active_scene()

        # get collection
        if collection_name:
            collection = XRFeitoriaBlenderFactory.get_collection(collection_name)
            if collection_name not in scene.collection.children.keys():
                raise RuntimeError(
                    f"Collection '{collection_name}' does not exist in the current active scene, please link it to active scene first."
                )
        else:
            collection = XRFeitoriaBlenderFactory.get_active_collection()

        # set 'collection' and 'scene' active
        XRFeitoriaBlenderFactory.set_scene_active(scene)
        XRFeitoriaBlenderFactory.set_collection_active(collection)

        return scene, collection

    def get_rotation_to_look_at(location: 'Tuple3', target: 'Tuple3') -> 'Tuple3':
        """Get the rotation of an object to look at another object.

        Args:
            location (Tuple3): Location of the object.
            target (Tuple3): Location of the target.

        Returns:
            Tuple3: Rotation of the object.
        """
        import mathutils

        direction = mathutils.Vector(target) - mathutils.Vector(location)
        rot_quat = direction.to_track_quat('-Z', 'Y')
        return rot_quat.to_euler()

    def get_all_object_in_seq(seq_name: str, obj_type: Literal['MESH', 'ARMATURE', 'CAMERA']) -> List['str']:
        """Get all objects in the sequence with the given type, and return their names.

        Args:
            obj_type (Literal['MESH', 'ARMATURE', 'CAMERA']): Type of the objects.

        Returns:
            List[str]: Names of the objects.
        """
        seq_collection = XRFeitoriaBlenderFactory.get_collection(seq_name)
        names = [obj.name for obj in seq_collection.objects if obj.type == obj_type]
        return names

    def get_all_object_in_current_level(obj_type: 'Literal["MESH", "ARMATURE", "CAMERA"]') -> 'List[str]':
        """Get all objects in active scene with the given type, and return their names.

        Args:
            obj_type (Literal['MESH', 'ARMATURE', 'CAMERA']): Type of the objects.

        Returns:
            List[str]: Names of the objects.
        """
        return [obj.name for obj in bpy.context.scene.objects if obj.type == obj_type]

    # --------- SET  -----------
    def set_scene_active(scene: 'bpy.types.Scene') -> None:
        """Set the given scene as the active scene.

        Args:
            scene (bpy.types.Scene): The scene to be set as the active scene.
        """
        bpy.context.window.scene = scene

    def set_collection_active(collection: 'bpy.types.Collection') -> None:
        """Set the given collection as the active collection.

        Args:
            collection (bpy.types.Collection): The collection to be set as the active collection.
        """
        if collection.name in bpy.context.view_layer.layer_collection.children.keys():
            layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]
            bpy.context.view_layer.active_layer_collection = layer_collection
        elif collection.name == bpy.context.view_layer.layer_collection.name:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection

    def set_frame_range(scene: 'bpy.types.Scene', start: int, end: int) -> None:
        """Set the frame range of the given scene.

        Args:
            scene (bpy.types.Scene): Scene.
            start (int): Start frame.
            end (int): End frame.
        """
        scene.frame_start = start
        scene.frame_end = end
        sequence_collection = scene.level_properties.active_sequence
        if sequence_collection:
            sequence_collection.sequence_properties.frame_start = start
            sequence_collection.sequence_properties.frame_end = end

    def set_frame_current(scene: 'bpy.types.Scene', frame: int) -> None:
        """Set the current frame of the given scene.

        Args:
            scene (bpy.types.Scene): Scene.
            frame (int): Current frame.
        """
        scene.frame_current = frame
        sequence_collection = scene.level_properties.active_sequence
        if sequence_collection:
            sequence_collection.sequence_properties.frame_current = frame

    def set_hdr_map(
        scene: 'bpy.types.Scene',
        hdr_map_path: str,
    ):
        """Set HDRI background in blender.

        Args:
            hdr_file_path (Path): filepath of the HDRI image
        """

        # Get the environment node tree of the current scene
        scene_world = bpy.data.worlds.new(name=scene.name)
        scene.world = scene_world
        scene.world.use_nodes = True
        node_tree = scene.world.node_tree
        tree_nodes = node_tree.nodes
        tree_nodes.clear()  # Clear all nodes

        node_background = tree_nodes.new(type='ShaderNodeBackground')  # Add Background node
        node_environment = tree_nodes.new('ShaderNodeTexEnvironment')  # Add Environment Texture node
        node_environment.image = bpy.data.images.load(hdr_map_path)  # Load and assign the image to the node property
        node_environment.location = -300, 0

        node_output = tree_nodes.new(type='ShaderNodeOutputWorld')  # Add Output node
        node_output.location = 200, 0

        # Link all nodes
        links = node_tree.links
        links.new(node_environment.outputs['Color'], node_background.inputs['Color'])
        links.new(node_background.outputs['Background'], node_output.inputs['Surface'])

    def set_multiview(scene: 'bpy.types.Scene') -> None:
        """Set the multiview of the scene.

        Args:
            scene (bpy.types.Scene): Scene.
        """
        if not scene.render.use_multiview:
            scene.render.use_multiview = True
            scene.render.views_format = 'MULTIVIEW'
            scene.render.views[0].use = False
            scene.render.views[1].use = False

    # --------- LINK  -----------
    def link_collection_to_scene(
        collection: 'bpy.types.Collection',
        scene: 'bpy.types.Scene',
    ) -> None:
        """Link a collection to a scene.

        Args:
            collection (bpy.types.Collection): Collection.
            scene (bpy.types.Scene): Scene.
        """
        if collection.name not in scene.collection.children.keys():
            scene.collection.children.link(collection)

    def unlink_collection_from_scene(
        collection: 'bpy.types.Collection',
        scene: 'bpy.types.Scene',
    ) -> None:
        """Unlink a collection from a scene.

        Args:
            collection (bpy.types.Collection): Collection.
            scene (bpy.types.Scene): Scene.
        """
        if collection.name in scene.collection.children.keys():
            scene.collection.children.unlink(collection)

    # --------- DELETE  -----------
    def delete_sequence(seq_name: str) -> None:
        """Delete a sequence. (Delete the scene and the collection named 'seq_name')

        Args:
            seq_name (str): Name of the sequence.
        """
        if seq_name in bpy.data.collections.keys():
            # delete all objects in seq_collection
            seq_collection = XRFeitoriaBlenderFactory.get_collection(name=seq_name)
            for obj in seq_collection.objects:
                bpy.data.objects.remove(obj)
            # delete seq_collection
            bpy.data.collections.remove(seq_collection)

    def delete_all():
        """Deletes all objects/collections/scenes in the current blend file."""
        # Delete all objects
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)

        # Delete all collections
        for coll in bpy.data.collections:
            bpy.data.collections.remove(coll)

        # Delete all scenes except for the last one
        for scene in bpy.data.scenes[:-1]:
            bpy.data.scenes.remove(scene)

        # Delete all renderviews in the last scene
        for view in bpy.context.scene.render.views:
            if view.name == 'left' or view.name == 'right':
                continue
            bpy.context.scene.render.views.remove(view)

    # --------- EXPORT  -----------
    def export_vertices(scene: 'bpy.types.Scene', export_path: str, use_animation: bool = True) -> None:
        """Export all the meshes' vertices of the scene to npz files.

        Args:
            scene (bpy.types.Scene): Scene to export vertices.
            export_path (str): Path to save the export npz files. (Require a folder)
            use_animation (bool, optional): Export the vertices positions of every frame if 'use_animation=True'. Defaults to True.
        """
        export_path = Path(export_path).resolve()
        export_path.mkdir(exist_ok=True, parents=True)
        for obj in scene.objects:
            if obj.type == 'MESH':
                XRFeitoriaBlenderFactory.triangulate_mesh(obj=obj)
                obj_export_path = export_path / f'{obj.name}.npz'
                logger.info(f'Exporting vertices of {obj.name} to "{obj_export_path.as_posix()}"')
                XRFeitoriaBlenderFactory.export_obj_vertices(
                    objs=obj, scene=scene, export_path=obj_export_path, use_animation=use_animation
                )

    #####################################
    ############### Mesh ################
    #####################################
    def triangulate_mesh(obj: 'bpy.types.Object', quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY') -> None:
        """Triangulate mesh, convert all quads to triangles.

        Args:
            obj (bpy.types.Object): The object to be triangulated.
            quad_method (str, optional): Quad Method, Method for splitting the quads into triangles. Defaults to 'SHORTEST_DIAGONAL'.
                Refer detailed explanation to https://docs.blender.org/api/current/bpy.ops.mesh.html#bpy.ops.mesh.quads_convert_to_tris.
            ngon_method (str, optional): N-gon Method, Method for splitting the n-gons into triangles. Defaults to 'BEAUTY'.
                Refer detailed explanation to https://docs.blender.org/api/current/bpy.ops.mesh.html#bpy.ops.mesh.quads_convert_to_tris.
        """
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method=quad_method, ngon_method=ngon_method)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)

    def get_bmesh_vertices(obj: 'bpy.types.Object', in_world_coors: bool = False) -> 'Tuple[np.ndarray, np.ndarray]':
        """Get local vertex locations from mesh with armature.

        Args:
            obj (bpy.types.Object): The object.
            in_world_coors (bool, optional): Get the vertices in world coordinates.
                                            Defaults to False.

        Returns:
            np.ndarray: vertices. each row is a vertex with x,y,z coordinates
            np.ndarray: faces. each row is a face with vertex indices
        """
        import bmesh

        depsgraph = bpy.context.evaluated_depsgraph_get()
        bm = bmesh.new()
        bm.from_object(obj, depsgraph)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        verts = [v.co for v in bm.verts]
        if in_world_coors:
            # Get the world matrix
            mat = obj.matrix_world
            # Get the geometry in world coordinates
            verts = [mat @ v for v in verts]
        verts = np.array(verts)
        faces = np.array([[v.index for v in f.verts] for f in bm.faces])

        # convert to opencv coordinate
        blender2opencv = lambda x: np.stack([x[:, 0], -x[:, 2], x[:, 1]], axis=-1)
        verts = blender2opencv(verts)
        return verts, faces

    def get_verts_and_faces(objs: 'List[bpy.types.Object]'):
        """Get verts and faces from objs, in world space. Join all objects into a single
        mesh, and return the vertices and faces.

        Args:
            objs (List[bpy.types.Object]): Object(s) to export
        """
        _verts = []
        _faces = []
        for obj in objs:
            _v, _f = XRFeitoriaBlenderFactory.get_bmesh_vertices(obj, in_world_coors=True)
            _verts.append(_v)
            _faces.append(_f)
        _verts = np.concatenate(_verts, axis=0)
        _faces = np.concatenate(_faces, axis=0)
        return _verts, _faces

    def export_obj_vertices(
        objs: Union['bpy.types.Object', List['bpy.types.Object']],
        scene: 'bpy.types.Scene',
        export_path: str,
        use_animation: bool = True,
    ) -> None:
        """Export verts in world space to npz file, with animation (export N frame) if
        use_animation is True. export_path will be an npz file with a single key 'verts'
        which is a numpy array in shape of (N, V, 3), where N is the number of frames, V
        is the number of vertices.

        Args:
            objs_name (Union[str, List[str]]): Object(s) to export
            export_path (str): Output file path
            use_animation (bool, optional): Export animation. Defaults to True.
        """
        if isinstance(objs, str):
            objs = [objs]
        if isinstance(objs, bpy.types.Object):
            objs = [objs]

        export_path = Path(export_path).resolve()
        export_path.parent.mkdir(exist_ok=True, parents=True)
        if use_animation:
            verts = []
            faces = []
            for frame_idx in range(scene.frame_start, scene.frame_end + 1):
                scene.frame_current = frame_idx
                _verts, _faces = XRFeitoriaBlenderFactory.get_verts_and_faces(objs)
                verts.append(_verts)
                faces.append(_faces)
            scene.frame_current = scene.frame_start
            verts = np.stack(verts, axis=0)
            faces = np.stack(faces, axis=0)
        else:
            _verts, _faces = XRFeitoriaBlenderFactory.get_verts_and_faces(objs)
            verts = np.expand_dims(_verts, axis=0)
            faces = np.expand_dims(_faces, axis=0)
        np.savez_compressed(str(export_path), verts=verts, faces=faces)

    #####################################
    ############## Renderer #############
    #####################################
    def render(scene: str = None) -> None:
        """Render the scene with default settings.

        Args:
            scene (str): Scene.
        """
        # XRFeitoriaBlenderFactory.get_scene(scene).render.use_multiview = True
        if scene is None:
            scene = XRFeitoriaBlenderFactory.get_active_scene().name
        bpy.ops.render.render(write_still=True, animation=True, scene=scene)

    def add_render_passes(output_path: str, render_passes: 'List[Dict[str, str]]', scene: 'bpy.types.Scene') -> None:
        bpy.context.window.scene = scene
        for render_pass in render_passes:
            bpy.ops.wm.add_render_pass(
                output_path=output_path,
                render_layer=render_pass['render_layer'],
                format=render_pass['image_format'],
            )

    def set_background_transparent(scene: 'bpy.types.Scene', transparent: bool = False) -> None:
        """Set the background of the scene to transparent.

        Args:
            scene (bpy.types.Scene): Scene.
            transparent (bool, optional): Transprant image background. Defaults to False.
        """
        if transparent:
            scene.render.dither_intensity = 0.0
        scene.render.film_transparent = transparent

    def enable_gpu(
        device_type: 'Literal["CUDA", "OPTIX", "HIP", "ONEAPI", "METAL", "NONE"]' = 'CUDA',
        gpu_num: int = 1,
    ) -> None:
        """Enable GPU devices for rendering.

        Args:
            device_type (str, optional): Device type. Defaults to 'CUDA'.
            gpu_num (int, optional): Number of GPUs to be used. Defaults to 1.
        """
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons['cycles'].preferences
        device_orders = ['CUDA', 'OPTIX', 'HIP', 'ONEAPI', 'METAL', 'NONE']
        # newer than 3.0
        if bpy.app.version[0] >= 3:

            def get_devices(device_type: str) -> List[Any]:
                try:
                    devices = cycles_preferences.get_devices_for_type(compute_device_type=device_type)
                    return devices
                except ValueError:
                    pass
                return []

            cycles_preferences.refresh_devices()
            devices = get_devices(device_type)
            if len(devices) == 0:
                logger.warning(f'No `{device_type}` devices found. Trying to use other devices.')
                for device_type in device_orders:
                    devices = get_devices(device_type)
                    if len(devices) > 0:
                        break
        # for version 2.X
        else:
            cuda_devices, opencl_devices = cycles_preferences.get_devices()
            device_type = device_orders[0] if device_type is None else device_type
            if device_type == 'CUDA':
                devices = cuda_devices
            elif device_type == 'OPENCL':
                devices = opencl_devices
            else:
                raise RuntimeError('Unsupported device type')
        # enable devices
        activated_gpus = []
        logger.info(f'Found `{device_type}` devices: {[device.name for device in devices]}')
        cpu_devices = [device for device in devices if device.type == 'CPU']
        gpu_devices = [device for device in devices if device.type == device_type]
        # strip gpu_devices
        gpu_devices = gpu_devices[:gpu_num]
        for device in cpu_devices:
            logger.info(f'CPU Device enabled: {device.name}')
            device.use = True
        for device in gpu_devices:
            logger.info(f'GPU Device enabled: {device.name}')
            device.use = True
            activated_gpus.append(device.name)

        if len(activated_gpus) <= 0:
            logger.warning('Failed to enable GPU. Going to use CPU only')
        else:
            cycles_preferences.compute_device_type = device_type
            bpy.context.scene.cycles.device = 'GPU'

    def set_resolution(scene: 'bpy.types.Scene', resolution: Tuple[int, int]) -> None:
        """Set resolution of the render images in the given scene.

        Args:
            scene (bpy.types.Scene): Scene.
            resolution (Tuple[int, int]): Image resolution.
        """
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]
        scene.render.resolution_percentage = 100

    def set_render_engine(engine: str, scene: 'bpy.types.Scene') -> None:
        """Set the render engine of the scene.

        Args:
            scene (bpy.types.Scene): Scene.
            engine (str, enum in ['CYCLES', 'BLENDER_EEVEE']): Render engine.
        """
        assert engine in ['CYCLES', 'BLENDER_EEVEE'], 'Invalid engine, must be `CYCLES` or `BLENDER_EEVEE`'
        scene.render.engine = engine

    def set_render_samples(render_samples: int, scene: 'bpy.types.Scene') -> None:
        """Set the render samples of the given scene.

        Args:
            render_samples (int): Render samples
            scene (bpy.types.Scene): Scene.
        """
        if scene.render.engine == 'CYCLES':
            scene.cycles.samples = render_samples
            # self.scene.cycles.time_limit = 20
        elif scene.render.engine == 'BLENDER_EEVEE':
            scene.eevee.taa_render_samples = render_samples

    #####################################
    ############### Camera ##############
    #####################################
    def get_resolution_from_blender() -> Tuple[int, int]:
        """Get resolution of the camera.

        Returns:
            Tuple[int, int]: Resolution.
        """
        scene = bpy.context.scene
        resolution_x_in_px = scene.render.resolution_x
        resolution_y_in_px = scene.render.resolution_y
        return resolution_x_in_px, resolution_y_in_px

    def get_3x3_K_matrix_from_blender(cam: 'bpy.types.Object') -> 'np.ndarray':
        """Get intrisic matrix (K) of a camera.

        Args:
            cam (bpy.types.Object): Camera.

        Returns:
            np.ndarray: K.
        """
        scene = bpy.context.scene
        fov = cam.data.angle

        resolution_x_in_px = scene.render.resolution_x
        resolution_y_in_px = scene.render.resolution_y

        focal = max(resolution_x_in_px, resolution_y_in_px) / 2 / math.tan(fov / 2)
        u_0 = resolution_x_in_px / 2
        v_0 = resolution_y_in_px / 2

        K = np.array(((focal, 0, u_0), (0, focal, v_0), (0, 0, 1)))
        return K

    def get_R_T_matrix_from_blender(cam: 'bpy.types.Object') -> 'Tuple[np.ndarray, np.ndarray]':
        """Get extrinsic parameters (R, T) of a camera.

        Args:
            cam (bpy.types.Object): Camera.

        Returns:
            Tuple[np.array, np.array]: R, T.
        """
        R_BlenderView_to_OpenCVView = np.diag([1, -1, -1])

        location, rotation = cam.matrix_world.decompose()[:2]
        R_BlenderView = rotation.to_matrix().transposed()

        T_BlenderView = -1.0 * R_BlenderView @ location

        R = R_BlenderView_to_OpenCVView @ R_BlenderView
        T = R_BlenderView_to_OpenCVView @ T_BlenderView

        return R, T

    def get_camera_KRT_from_blender(cam: 'bpy.types.Object') -> 'Tuple[np.ndarray, np.ndarray, np.ndarray]':
        """Get camera KRT from blender camera object.

        Args:
            cam (bpy.types.Object): Camera.

        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray]: K, R, T.
        """
        import mathutils

        K = XRFeitoriaBlenderFactory.get_3x3_K_matrix_from_blender(cam)
        R, T = XRFeitoriaBlenderFactory.get_R_T_matrix_from_blender(cam)

        # -90 deg rotation around x axis, to convert from blender to opencv coordinate system
        _R = mathutils.Matrix(R)
        _R_euler = _R.to_euler('XYZ')
        _R_euler.x -= math.pi / 2
        R = np.asarray(_R_euler.to_matrix())
        return K, R, T

    def add_multiview_camera(camera_name: str, scene: 'bpy.types.Scene') -> None:
        """Add a multiview camera to the scene.

        Args:
            camera_name (str): Name of the camera.
            scene (bpy.types.Scene): Scene.
        """
        if camera_name not in scene.render.views.keys():
            render_view = scene.render.views.new(camera_name)
            render_view.file_suffix = camera_name
            render_view.camera_suffix = camera_name

    def set_camera_activity(camera_name: str, scene: 'bpy.types.Scene', active: bool) -> None:
        """Set the activity of the given camera.

        Args:
            camera_name (str): Name of the camera.
            scene (bpy.types.Scene): Scene.
            active (bool, optional): Activity of this multiview camera.
        """
        XRFeitoriaBlenderFactory.set_multiview(scene)
        XRFeitoriaBlenderFactory.add_multiview_camera(camera_name=camera_name, scene=scene)
        render_view = scene.render.views[camera_name]
        render_view.use = active

    def get_active_cameras(scene: 'bpy.types.Scene') -> List[str]:
        """Get all active cameras of the given scene.

        Args:
            scene (bpy.types.Scene): Scene.

        Returns:
            List[str]: Name of the active cameras.
        """
        active_cameras = []
        for cam in scene.render.views:
            if cam.use is True:
                active_cameras.append(cam.camera_suffix)
        return active_cameras

    #####################################
    ############### Import ##############
    #####################################
    def import_texture(texture_file: str) -> bpy.types.Image:
        """Import an image as a texture.

        Args:
            texture_file (str): File path of the image.
        Returns:
            bpy.types.Image: The imported texture.
        """
        try:
            texture = bpy.data.images.load(filepath=str(texture_file))
        except Exception:
            raise Exception(f'Failed to import texture: {texture_file}')
        return texture

    def import_fbx(fbx_file: str) -> None:
        """Import an fbx file. Only support binary fbx.
        Ref: https://docs.blender.org/manual/en/3.6/addons/import_export/scene_fbx.html#id4

        Args:
            fbx_file (str): File path of the fbx file.
        """
        try:
            bpy.ops.import_scene.fbx(filepath=str(fbx_file))
        except Exception as e:
            raise Exception(f'Failed to import fbx: {fbx_file}\n{e}')

    def import_obj(obj_file: str) -> None:
        """Import an obj file.

        Args:
            obj_file (str): File path of the obj file.
        """
        try:
            bpy.ops.import_scene.obj(filepath=str(obj_file))
        except Exception:
            raise Exception(f'Failed to import obj: {obj_file}')

    def import_alembic(alembic_file: str) -> None:
        """Import an existing alembic animation into blender."""
        try:
            bpy.ops.wm.alembic_import(filepath=str(alembic_file), relative_path=False, as_background_job=False)
        except Exception as e:
            raise Exception(f'Failed to import alembic: {alembic_file}, error: {e}')

    def import_ply(ply_file: str) -> None:
        """Import an ply file.

        Args:
            ply_file (str): File path of the ply file.
        """
        try:
            bpy.ops.import_mesh.ply(filepath=str(ply_file))
        except Exception as e:
            raise Exception(f'Failed to import ply: {ply_file}\n{e}')

    def import_stl(stl_file: str) -> None:
        """Import an stl file.

        Args:
            stl_file (str): File path of the stl file.
        """
        try:
            bpy.ops.import_mesh.stl(filepath=str(stl_file))
        except Exception as e:
            raise Exception(f'Failed to import stl: {stl_file}\n{e}')

    def import_glb(glb_file: str) -> None:
        """Import an glb file.

        Args:
            glb_file (str): File path of the glb file.
        """
        try:
            bpy.ops.import_scene.gltf(filepath=str(glb_file))
        except Exception as e:
            raise Exception(f'Failed to import glb: {glb_file}\n{e}')

    def import_mo_json(mo_json_file: Path, actor_name: str) -> None:
        """Import an animation from json, and apply the animation to the given actor. In
        form of quaternion.

        Args:
            mo_json_file (Path): json file path.
            actor_name (str): Name of the actor.
        """
        with open(mo_json_file, 'r') as f:
            motion_data = json.load(f)
        XRFeitoriaBlenderFactory.apply_motion_data_to_actor(motion_data, actor_name=actor_name)

    def import_mo_blend(mo_blend_file: Path, action_name: str, actor_name: str) -> None:
        """Import an animation from blend, and apply the animation to the given actor.

        Args:
            mo_json_file (Path): blend file path.
            actor_name (str): Name of the actor.
        """
        with bpy.data.libraries.load(mo_blend_file) as (data_from, data_to):
            data_to.actions.append(action_name)
        action = bpy.data.actions[action_name]
        actor = bpy.data.objects[actor_name]
        XRFeitoriaBlenderFactory.apply_action_to_actor(action, actor)

    def import_mo_fbx(mo_fbx_file: Path, actor_name: str) -> None:
        """Import an animation from fbx, and apply the animation to the given actor.

        Args:
            mo_json_file (Path): fbx file path.
            actor_name (str): Name of the actor.
        """
        mo_object_name = 'tmp_import_action'
        with XRFeitoriaBlenderFactory.__judge__(
            name=mo_object_name, import_path=mo_fbx_file, scene=XRFeitoriaBlenderFactory.get_active_scene()
        ):
            XRFeitoriaBlenderFactory.import_fbx(mo_fbx_file)
        action = bpy.data.objects[mo_object_name].animation_data.action
        actor = bpy.data.objects[actor_name]
        XRFeitoriaBlenderFactory.apply_action_to_actor(action, actor)
        bpy.data.objects.remove(bpy.data.objects[mo_object_name])

    def apply_action_to_actor(action: 'bpy.types.Action', actor: 'bpy.types.Object') -> None:
        """Apply action to object.

        Args:
            action (bpy.types.Action): Action
            actor (bpy.types.Object): Actor
        """
        if actor.animation_data:
            actor.animation_data_clear()
        actor.animation_data_create()
        actor.animation_data.action = action

    def apply_motion_data_to_action(
        motion_data: 'List[Dict[str, Dict[str, List[float]]]]',
        action: 'bpy.types.Action',
        scale: float = 1.0,
    ) -> None:
        """Apply motion data in dict to object.

        Args:
            motion_data (List[Dict[str, Dict]]): Motion data in the form of dict,
                containing rotation (quaternion) and location.
            action (bpy.types.Action): Action.
            scale (float, optional): Scale of movement in location of animation. Defaults to 1.0.
        """
        import numpy as np

        num_frames = len(motion_data)
        fcurves_map = {(fc.data_path, fc.array_index): fc for fc in action.fcurves}

        def _get_fcurve(data_path: str, index: int):
            key_ = (data_path, index)
            if key_ in fcurves_map:
                fcurve = fcurves_map[key_]
            else:
                fcurve = fcurves_map.setdefault(key_, action.fcurves.new(data_path, index=index))
                # fcurve.keyframe_points.add(num_frames)
            return fcurve

        # Set keyframes
        frames_iter = range(num_frames)
        loc0 = [0, 0, 0]
        for f in frames_iter:
            for bone_name in motion_data[0].keys():
                # rotation_quaternion
                data_path = f'pose.bones["{bone_name}"].rotation_quaternion'
                motion = motion_data[f][bone_name]
                for idx, val in enumerate(motion['rotation']):
                    fcurve = _get_fcurve(data_path=data_path, index=idx)
                    # fcurve.keyframe_points[f].co = (f, val)
                    fcurve.keyframe_points.insert(frame=f, value=val, options={'FAST'})
                    # if bone_name == "left_shoulder":
                    #     print(f, [list(x.co) for x in fcurve.keyframe_points])
                # location
                if 'location' in motion:
                    data_path = f'pose.bones["{bone_name}"].location'
                    location_ = motion['location']
                    if f < 1:
                        loc0 = location_
                        location_ = np.zeros(3)
                    else:
                        location_ = np.subtract(location_, loc0) * scale
                    for idx, val in enumerate(location_):
                        fcurve = _get_fcurve(data_path=data_path, index=idx)
                        # fcurve.keyframe_points[f].co = (f, val)
                        fcurve.keyframe_points.insert(frame=f, value=val, options={'FAST'})

    def apply_motion_data_to_actor(motion_data: 'List[Dict[str, Dict[str, List[float]]]]', actor_name: str) -> None:
        """Applies motion data to a given actor.

        Args:
            motion_data: A list of dictionaries containing motion data (quaternion) for the actor.
            actor_name: The name of the actor to apply the motion data to.
        """
        action = bpy.data.actions.new('Action')
        XRFeitoriaBlenderFactory.apply_motion_data_to_action(motion_data=motion_data, action=action)
        XRFeitoriaBlenderFactory.apply_action_to_actor(action, actor=bpy.data.objects[actor_name])

    #####################################
    ############# validate ##############
    #####################################

    @contextmanager
    def __judge__(name: str, scene: 'bpy.types.Scene', import_path: 'Optional[str]' = None):
        """Get the new imported/added objects, validate the new objects, and rename the
        new objects. \n If the new objects are not valid, raise ValueError. \n If the
        new objects are valid, rename the new objects to 'name'. \n If the new objects
        contain a mesh and an armature, rename the armature to 'name'.

        Args:
            name (str): Name of the new object in Blender.
            scene (bpy.types.Scene): Scene to add the new object to.
            import_path (Optional[str], optional): Import path. Defaults to None.

        Yields:
            None: None

        Raises:
            ValueError: If the new objects are not valid.

        Examples:
            >>> # in Blender
            >>> from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory
            >>> with XRFeitoriaBlenderFactory.__judge__(name='test'):
            ...    XRFeitoriaBlenderFactory.import_fbx('/usr/home/test.fbx')
            >>> actor = bpy.data.objects['test']
        """
        old_objs = set(scene.objects)
        yield
        new_objs = list(set(scene.objects) - old_objs)

        # record new_obj's matrix_world
        matrices_world = {}
        for new_obj in new_objs:
            if new_obj.type != 'EMPTY' and new_obj.parent is not None and new_obj.parent.type == 'EMPTY':
                bpy.context.view_layer.update()
                matrices_world[new_obj.name] = new_obj.matrix_world

        # delete empty
        new_objs_without_empty = []
        for new_obj in new_objs:
            if new_obj.type == 'EMPTY':
                bpy.data.objects.remove(new_obj)
            else:
                new_objs_without_empty.append(new_obj)

        # set matrix_world
        for new_obj in new_objs_without_empty:
            if new_obj.name in matrices_world.keys():
                new_obj.matrix_world = matrices_world[new_obj.name]
                bpy.context.view_layer.update()

        # validate and rename
        if not new_objs_without_empty:
            if import_path:
                raise ValueError(f"Failed to import from '{import_path}'")
            else:
                raise ValueError(f"Failed to spawn '{name}'.")
        elif len(new_objs_without_empty) == 1:
            new_obj = new_objs_without_empty[0]
            new_obj.name = name
            new_obj.rotation_mode = 'XYZ'
        elif len(new_objs_without_empty) >= 2:
            obj_types = [obj.type for obj in new_objs_without_empty]
            if 'ARMATURE' not in obj_types:
                raise ValueError('Unsupported file')
            elif obj_types.count('ARMATURE') >= 2:
                raise ValueError('Unsupported file')
            elif 'ARMATURE' in obj_types and 'MESH' in obj_types:
                new_obj = new_objs_without_empty[obj_types.index('ARMATURE')]
                new_obj.name = name
                new_obj.rotation_mode = 'XYZ'

    #####################################
    ############## Object ###############
    #####################################
    def get_bound_box_in_world_space(
        obj: 'bpy.types.Object',
    ) -> 'Tuple[Tuple[float, float, float], Tuple[float, float, float]]':
        """Get the bounding box of the object in world space.

        Args:
            obj (bpy.types.Object): Object.

        Raises:
            ValueError: If the object type is not mesh or armature.

        Returns:
            Tuple[Tuple[float, float, float], Tuple[float, float, float]]: Min and max point of the bounding box.
        """
        if obj.type == 'MESH':
            depsgraph = bpy.context.evaluated_depsgraph_get()
            evaluated_obj = obj.evaluated_get(depsgraph)
            evaluated_mesh = evaluated_obj.data

            vertex_positions = []
            for vertex in evaluated_mesh.vertices:
                vertex_position = obj.matrix_world @ vertex.co
                vertex_positions.append(vertex_position)

            bbox_min = (1e9, 1e9, 1e9)
            bbox_max = (-1e9, -1e9, -1e9)
            bbox_min = (
                min(bbox_min[0], min(pos.x for pos in vertex_positions)),
                min(bbox_min[1], min(pos.y for pos in vertex_positions)),
                min(bbox_min[2], min(pos.z for pos in vertex_positions)),
            )
            bbox_max = (
                max(bbox_max[0], max(pos.x for pos in vertex_positions)),
                max(bbox_max[1], max(pos.y for pos in vertex_positions)),
                max(bbox_max[2], max(pos.z for pos in vertex_positions)),
            )
            return bbox_min, bbox_max
        elif obj.type == 'ARMATURE':
            bbox_min = (1e9, 1e9, 1e9)
            bbox_max = (-1e9, -1e9, -1e9)
            for obj_mesh in obj.children:
                depsgraph = bpy.context.evaluated_depsgraph_get()
                evaluated_obj = obj_mesh.evaluated_get(depsgraph)
                evaluated_mesh = evaluated_obj.data

                vertex_positions = []
                for vertex in evaluated_mesh.vertices:
                    vertex_position = obj_mesh.matrix_world @ vertex.co
                    vertex_positions.append(vertex_position)

                bbox_min = (
                    min(bbox_min[0], min(pos.x for pos in vertex_positions)),
                    min(bbox_min[1], min(pos.y for pos in vertex_positions)),
                    min(bbox_min[2], min(pos.z for pos in vertex_positions)),
                )
                bbox_max = (
                    max(bbox_max[0], max(pos.x for pos in vertex_positions)),
                    max(bbox_max[1], max(pos.y for pos in vertex_positions)),
                    max(bbox_max[2], max(pos.z for pos in vertex_positions)),
                )
            return bbox_min, bbox_max
        else:
            raise ValueError(f'Invalid object type: {obj.type}')

    #####################################
    ############# Material ##############
    #####################################
    def get_material(mat_name: str) -> 'bpy.types.Material':
        if mat_name not in bpy.data.materials.keys():
            raise ValueError(f"Material '{mat_name}' does not exists in this blend file.")
        return bpy.data.materials[mat_name]

    def new_mat_node(mat: 'bpy.types.Material', type: str, name: Optional[str] = None) -> bpy.types.Node:
        _nodes = mat.node_tree.nodes
        node = _nodes.new(type=type)
        if name:
            node.name = name
        return node
