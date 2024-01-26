"""
>>> python -m samples.blender.04_staticmesh_render

This is a script to render static meshes in blender.
"""
import math
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.data_structure.models import SequenceTransformKey as SeqTransKey
from xrfeitoria.utils import setup_logger

from ..config import assets_path, blender_exec
from ..utils import visualize_vertices

root = Path(__file__).resolve().parents[2]
# output_path = '~/xrfeitoria/output/samples/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'blender.log'
output_blend_file = output_path / 'source.blend'

seq_1_name = 'Sequence_static_mesh_1'
seq_2_name = 'Sequence_static_mesh_2'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)

    #############################
    #### use default level ######
    #############################

    # open blender and automatically create a default level named `XRFeitoria`
    xf_runner = xf.init_blender(exec_path=blender_exec, background=background, new_process=True)

    # set hdr map
    xf_runner.utils.set_hdr_map(hdr_map_path=assets_path['hdr_sample'])

    # import an actor to the level
    actor_bunny = xf_runner.Actor.import_from_file(file_path=assets_path['bunny'], stencil_value=128)
    # set the origin of bunny to its center
    actor_bunny.set_origin_to_center()

    # set bunny's size to 0.4m
    bunny_size = 0.4
    bunny_max_dimensions = max(actor_bunny.dimensions)
    actor_bunny.scale = (bunny_size / bunny_max_dimensions,) * 3

    # add a new camera looking at the bunny, and the distance between them is 2m
    distance_to_bunny = 2
    camera = xf_runner.Camera.spawn(
        location=(
            actor_bunny.location[0],
            actor_bunny.location[1] - distance_to_bunny,
            actor_bunny.location[2],
        )
    )
    camera.look_at(actor_bunny.location)

    # set camera's fov to make the bunny fill the 10% of screen
    camera.fov = math.degrees(math.atan(((bunny_size * 0.5) / 0.1) / distance_to_bunny)) * 2

    ##################################################
    #### Create a new sequence with default level ####
    ##################################################
    with xf_runner.Sequence.new(seq_name=seq_1_name) as seq:
        # use the `camera` in level to render
        seq.use_camera(camera=camera)

        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path / seq_1_name,
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'png'),
            ],
            resolution=[512, 512],
            render_engine='CYCLES',
            render_samples=32,
            transparent_background=False,
            arrange_file_structure=True,
        )

    ########################################################
    #### Create another new sequence with default level ####
    ########################################################
    with xf_runner.Sequence.new(seq_name=seq_2_name) as seq:
        # import an actor to the sequence, and add transform keys to make it rotate around the bunny and grow bigger and bigger
        actor_kc = seq.import_actor(file_path=assets_path['koupen_chan'], stencil_value=255)
        actor_kc.set_origin_to_center()

        # get koupen_chan's rotation and size in the first frame
        kc_rotation = actor_kc.rotation
        kc_size = max(actor_kc.dimensions)
        bunny_location = actor_bunny.location

        # set koupen_chan's transform keys
        transform_keys = []
        for i in range(6):
            azimuth = 360 / 6 * i
            azimuth_radians = math.radians(azimuth)

            x = math.cos(azimuth_radians) + bunny_location[0]
            y = math.sin(azimuth_radians) + bunny_location[1]
            z = 0.0 + bunny_location[2]

            transform_keys.append(
                SeqTransKey(
                    frame=i,
                    location=(x, y, z),
                    rotation=(kc_rotation[0], kc_rotation[1], kc_rotation[2] + azimuth),
                    scale=(0.1 / kc_size * (i + 1),) * 3,
                    interpolation='AUTO',
                )
            )
        actor_kc.set_transform_keys(transform_keys=transform_keys)

        # use the `camera` in level to render
        seq.use_camera(camera=camera)

        # get keys range of all objects in the scene
        keys_range = xf_runner.utils.get_keys_range()
        # set frame range of the scene according to keys range
        xf_runner.utils.set_frame_range(start=keys_range[0], end=keys_range[1])

        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path,
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'png'),
            ],
            resolution=[512, 512],
            render_engine='CYCLES',
            render_samples=32,
            transparent_background=False,
            arrange_file_structure=True,
        )

        # export verts of meshes in this sequence and its level
        xf_runner.utils.export_vertices(export_path=output_path / seq_2_name / 'vertices')

    # render
    xf_runner.render()

    # Save the blender file to the current directory.
    xf_runner.utils.save_blend(save_path=output_blend_file)

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # collect the names for visualization
    camera_name = camera.name
    actor_names = [actor_bunny.name, actor_kc.name]

    # close the blender process
    xf_runner.close()

    seq1_out = output_path / seq_1_name / 'img' / camera_name / '0000.png'
    seq2_out = output_path / seq_2_name / 'img' / camera_name / '0003.png'
    logger.info(f'Check the output of seq_1 in "{seq1_out.as_posix()}"')
    logger.info(f'Check the output of seq_2 in "{seq2_out.as_posix()}"')

    visualize_vertices(
        camera_name=camera_name,
        actor_names=actor_names,
        seq_output_path=output_path / seq_2_name,
        frame_idx=5,
    )


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
