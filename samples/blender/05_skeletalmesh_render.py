"""
>>> python -m samples.blender.05_skeletalmesh_render

This is a script to render skeletal meshes in blender.
"""
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.data_structure.models import SequenceTransformKey as SeqTransKey

from ..config import assets_path, blender_exec
from ..utils import setup_logger

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/samples/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'blender.log'
output_blend_file = output_path / 'source.blend'

seq_name = 'Sequence_skeletal_mesh'


def main(debug=False, background=False):
    logger = setup_logger(debug=debug, log_path=log_path)

    #################################
    #### Define your own level ######
    #################################

    # open blender
    xf_runner = xf.init_blender(exec_path=blender_exec, background=background, new_process=False)

    # define a new level named `MyLevel`
    xf_runner.utils.new_level(name='MyLevel')

    ####################################################
    ### Create a new sequence with the defined level ###
    ####################################################
    seq_length = 200
    with xf_runner.Sequence.new(seq_name=seq_name, level='MyLevel', seq_length=seq_length) as seq:
        # import an skeletal mesh and set an animation to it
        actor = seq.import_actor(file_path=assets_path['SMPL_XL'], stencil_value=128)
        actor.setup_animation(animation_path=assets_path['motion_2'])

        # use a list to store the transform keys of the cameras
        transform_keys_tracking_camera = []

        for i in range(seq_length):
            # set current frame
            xf_runner.utils.set_frame_current(i)

            # get actor's bounding box at each frame
            bbox_min, bbox_max = actor.bound_box

            # set camera's location and rotation to track the actor
            actor_location = (
                (bbox_min[0] + bbox_max[0]) / 2,
                (bbox_min[1] + bbox_max[1]) / 2,
                (bbox_min[2] + bbox_max[2]) / 2,
            )
            camera_location = (actor_location[0], actor_location[1] - 2, actor_location[2])
            camera_rotation = xf_runner.utils.get_rotation_to_look_at(location=camera_location, target=actor_location)
            transform_keys_tracking_camera.append(
                SeqTransKey(
                    frame=i,
                    location=camera_location,
                    rotation=camera_rotation,
                    interpolation='AUTO',
                )
            )
            logger.info(f'Frame {i}: {camera_location}, {camera_rotation}')

        # add a camera in sequence to render
        camera = seq.spawn_camera_with_keys(transform_keys=transform_keys_tracking_camera, fov=90)

        # set environment color
        xf_runner.utils.set_env_color(color=(1, 1, 1, 1))

        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path / f'{seq.name}',
            render_passes=[
                RenderPass('img', 'png'),
                RenderPass('mask', 'png'),
            ],
            resolution=[512, 512],
            render_engine='CYCLES',
            render_samples=128,
            transparent_background=False,
            arrange_file_structure=True,
        )

    # render all jobs
    xf_runner.render()

    # Save the blender file to the current directory.
    xf_runner.utils.save_blend(save_path=output_blend_file)

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # close the blender process
    xf_runner.close()

    output_img = output_path / seq_name / 'img' / camera.name / '0000.png'
    if output_img.exists():
        logger.info(f'Check the output in "{output_img.as_posix()}"')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
