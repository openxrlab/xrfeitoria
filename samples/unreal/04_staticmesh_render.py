"""
>>> python -m samples.unreal.04_staticmesh_render

This is a script to render static meshes in unreal.
"""
import math
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.data_structure.models import SequenceTransformKey as SeqTransKey
from xrfeitoria.utils import setup_logger

from ..config import assets_path, unreal_exec, unreal_project
from ..utils import visualize_vertices

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/samples/unreal/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'unreal.log'

# pre-defined level
default_level_path = '/Game/Levels/Default'
level_path = '/Game/Levels/Playground'
seq_1_name = 'seq_staticmesh_1'
seq_2_name = 'seq_staticmesh_2'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)
    xf_runner = xf.init_unreal(exec_path=unreal_exec, project_path=unreal_project, background=background)

    # duplicate the level to a new level
    xf_runner.utils.open_level(default_level_path)  # in case {dst_level_path} already opened
    dst_level_path = f'{level_path}_staticmesh'

    xf_runner.utils.duplicate_asset(src_path=level_path, dst_path=dst_level_path, replace=True)
    xf_runner.utils.open_level(dst_level_path)

    # Usually, assets are pre-imported from files before rendering.
    koupen_chan_path = xf_runner.utils.import_asset(path=assets_path['koupen_chan'])
    # Or you can import assets from files directly to the current level.
    actor_bunny = xf_runner.Actor.import_from_file(file_path=assets_path['bunny'])

    # If you want to place assets and cameras, mostly you need to set them manually or based on logic.
    # It's easier to get more infos of the assets using blender, please refer to the blender samples if interested.
    # Hardcode: In this example, we hardcode the transform of the bunny and the camera.
    actor_bunny.scale = (10, 10, 10)  # set scale to 10x
    actor_bunny.rotation = (0, 0, 90)  # rotate 90 degrees around z axis

    # add a new camera looking at the bunny
    camera = xf_runner.Camera.spawn(location=(-5, 0, 2))
    camera.look_at(actor_bunny.location)

    # save the level
    xf_runner.utils.save_current_level()

    # clear the renderer
    xf_runner.Renderer.clear()

    # If you want to add new objects(cameras, actors, shapes) with transform keys, use sequence.
    ####################################################
    ######## Create a new sequence with level   ########
    ####################################################
    with xf_runner.Sequence.new(level=dst_level_path, seq_name=seq_1_name, replace=True) as seq:
        # show the sequence in unreal editor
        seq.show()
        # use the `camera` in level to render
        seq.use_camera(camera=camera, location=(-5, 0, 2))

        # use the `bunny` in level
        seq.use_actor(actor_bunny, scale=(10, 10, 10), rotation=(0, 0, 90), stencil_value=1)

        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path,
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'exr'),  # in png format, annotations would apply gamma correction (2.2)
            ],
            console_variables={'r.MotionBlurQuality': 0},  # disable motion blur
            resolution=[1280, 720],
            export_vertices=True,
        )

    ####################################################
    ##### Create another new sequence with level   #####
    ####################################################
    with xf_runner.Sequence.new(level=dst_level_path, seq_name=seq_2_name, seq_length=6, replace=True) as seq:
        # show the sequence in unreal editor
        seq.show()

        # define transform keys of rotating around the bunny
        transform_keys = []
        bunny_location = actor_bunny.location
        for idx in range(6):
            radius = 2.0
            azimuth = 360 / 6 * idx
            azimuth_radians = math.radians(azimuth)

            x = radius * math.cos(azimuth_radians) + bunny_location[0]
            y = radius * math.sin(azimuth_radians) + bunny_location[1]
            z = 0.0 + bunny_location[2]

            scale = 0.05
            transform_keys.append(
                SeqTransKey(frame=idx, location=(x, y, z), scale=(scale, scale, scale), interpolation='AUTO')
            )

        # spawn koupen_chan with transform keys to the sequence
        actor_kc = seq.spawn_actor_with_keys(koupen_chan_path, transform_keys=transform_keys, stencil_value=2)

        # use the `camera` in level to render
        seq.use_camera(camera=camera, location=(-5, 0, 2))

        # use the `bunny` in level
        seq.use_actor(actor_bunny, scale=(10, 10, 10), rotation=(0, 0, 90), stencil_value=3)

        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path,
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'exr'),  # in png format, annotations would apply gamma correction (2.2)
            ],
            console_variables={'r.MotionBlurQuality': 0},  # disable motion blur
            resolution=[1280, 720],
            export_vertices=True,
        )

        # collect the names for visualization
        camera_name = camera.name
        actor_names = [actor_bunny.name, actor_kc.name]

    # render jobs
    xf_runner.render()

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    xf_runner.close()

    # visualize vertices of the actors
    visualize_vertices(
        camera_name=camera_name,
        actor_names=actor_names,
        seq_output_path=output_path / seq_2_name,
        frame_idx=0,
    )


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
