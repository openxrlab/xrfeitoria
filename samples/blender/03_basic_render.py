"""
>>> python -m samples.blender.03_basic_render

This is a script to render a preset level in blender.
"""
from pathlib import Path

import xrfeitoria as xf
from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.utils import setup_logger

from ..config import assets_path, blender_exec

root = Path(__file__).parents[2].resolve()
# output_path = '~/xrfeitoria/output/samples/blender/{file_name}'
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
log_path = output_path / 'blender.log'
output_blend_file = output_path / 'source.blend'

seq_name = 'Sequence'


def main(debug=False, background=False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO', log_path=log_path)

    ################################################################################################################################
    # In XRFeitoria, a `level` is an editable space that can be used to place objects(3D models, lights, cameras, etc.),
    # and a `sequence` is a collection of objects in `level` that can be rendered together.

    # The objects in a `level` are shared by all `sequence`s in this `level`,
    # and the objects in a `sequence` are independent of other `sequence`s in this `level`.
    # Therefore, rendering should be performed on a `sequence` basis.

    # In blender, a `level` is a `scene`, and a `sequence` is a `collection` in the `scene`.
    # The default level is named `XRFeitoria`, and it is automatically created when the blender is started.
    # The operations in the previous examples are all performed in the default level.
    # You can also use other preset levels downloaded from the internet, or create your own level by xf_runner.utils.new_level().

    # The following example demonstrates how to use a preset level to render a scene.
    ################################################################################################################################

    # open the specified .blend file given by `project_path`, and the scene `Scene` is a `level`.
    xf_runner = xf.init_blender(
        exec_path=blender_exec,
        background=background,
        new_process=True,
        cleanup=False,
        project_path=assets_path['blend_sample'],
    )

    # by creating a new `sequence`, XRFeitoria links a new collection named `{seq_name}` to the level.
    with xf_runner.Sequence.new(seq_name=seq_name, level='Scene') as seq:
        # The cameras in the level will not be used for rendering by default,
        # but you can activate them by calling `seq.use_camera(camera)`.
        # There is a camera named `Camera` in the level, and we use it for rendering.
        camera = xf_runner.Camera('Camera')
        camera_name = camera.name
        seq.use_camera(camera)

        # add render job to renderer
        seq.add_to_renderer(
            output_path=output_path,
            render_passes=[RenderPass('img', 'png')],
            resolution=[512, 512],
            render_engine='CYCLES',
            render_samples=32,
            transparent_background=False,
            arrange_file_structure=True,
        )

    # render
    xf_runner.render()

    # Save the blender file to the current directory.
    xf_runner.utils.save_blend(save_path=output_blend_file)

    logger.info('🎉 [bold green]Success!')
    input('Press Any Key to Exit...')

    # close the blender process
    xf_runner.close()

    output_img = output_path / seq_name / 'img' / camera_name / '0000.png'
    if output_img.exists():
        logger.info(f'Check the output in "{output_img}"')


if __name__ == '__main__':
    from ..utils import parse_args

    args = parse_args()

    main(debug=args.debug, background=args.background)
