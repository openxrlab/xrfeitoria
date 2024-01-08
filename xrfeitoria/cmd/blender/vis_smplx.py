"""Install a blender plugin with a command line interface.

>>> xf-install-plugin --help
>>> xf-render {} [-o {output_path}]
"""

from pathlib import Path
from textwrap import dedent
from typing import Tuple

import xrfeitoria as xf
from xrfeitoria.rpc import remote_blender
from xrfeitoria.utils import setup_logger

try:
    import numpy as np
    from typer import Argument, Option, Typer
    from typing_extensions import Annotated

    from xrfeitoria.utils.anim.motion import Motion, SMPLMotion, SMPLXMotion
except (ImportError, NameError):
    pass

app = Typer(pretty_exceptions_show_locals=False)


@remote_blender()
def add_smplx(betas: 'Tuple[float, ...]' = [0.0] * 10, gender: str = 'neutral') -> str:
    """Add smplx mesh to scene and return the name of the armature and the mesh.

    Args:
        betas (Tuple[float, ...]): betas of smplx model
        gender (str): gender of smplx model

    Returns:
        str: armature name
    """
    import bpy

    assert hasattr(bpy.ops.scene, 'smplx_add_gender'), 'Please install smplx addon first'

    bpy.data.window_managers['WinMan'].smplx_tool.smplx_gender = gender
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_handpose = 'flat'
    bpy.ops.scene.smplx_add_gender()

    bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_f_alb.png'
    bpy.ops.object.smplx_set_texture()

    smplx_mesh = bpy.context.selected_objects[0]
    for index, beta in enumerate(betas):
        smplx_mesh.data.shape_keys.key_blocks[f'Shape{index:03d}'].value = beta
    bpy.ops.object.smplx_update_joint_locations()
    bpy.ops.object.smplx_set_handpose()

    return smplx_mesh.parent.name


@remote_blender()
def export_fbx(
    tgt_rig_name: str,
    save_path: 'Path',
    with_mesh: bool = False,
    use_better_fbx: bool = True,
    **options,
) -> bool:
    import bpy

    if use_better_fbx and not hasattr(bpy.ops, 'better_export'):
        raise RuntimeError('Unable to found better_fbx addon!')

    target_rig = bpy.data.objects[tgt_rig_name]

    save_path = Path(save_path).resolve()
    bpy.ops.object.mode_set(mode='OBJECT')
    # re-select the armature
    # bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = target_rig
    if with_mesh:
        # select the mesh for export
        bpy.ops.object.select_grouped(type='CHILDREN_RECURSIVE')
    target_rig.select_set(True)

    if save_path.exists():
        ctime = save_path.stat().st_ctime
    else:
        ctime = 0

    save_path.parent.mkdir(exist_ok=True, parents=True)
    save_path_str = str(save_path)
    if use_better_fbx:
        bpy.ops.better_export.fbx(filepath=save_path_str, use_selection=True, **options)
    else:
        bpy.ops.export_scene.fbx(filepath=save_path_str, use_selection=True, **options)

    if save_path.exists() and save_path.stat().st_ctime > ctime:
        success = True
    else:
        success = False
    return success


def read_smpl_x(path: Path) -> 'Motion':
    """Reads a SMPL/SMPLX motion from a .npz file.

    Args:
        path (Path): Path to the .npz file.

    Returns:
        SMPLXMotion: The motion.
    """
    smpl_x_data = np.load(path, allow_pickle=True)
    if 'smplx' in smpl_x_data:
        smpl_x_data = smpl_x_data['smplx'].item()
        motion = SMPLXMotion.from_smplx_data(smpl_x_data)
    if 'smpl' in smpl_x_data:
        smpl_x_data = smpl_x_data['smpl'].item()
        motion = SMPLMotion.from_smpl_data(smpl_x_data)
    if 'pose_body' in smpl_x_data:
        motion = SMPLXMotion.from_amass_data(smpl_x_data, insert_rest_pose=False)
    else:
        try:
            motion = SMPLXMotion.from_smplx_data(smpl_x_data)
        except Exception:
            raise ValueError(f'Unknown data format of {path}, got {smpl_x_data.keys()}, but expected "smpl" or "smplx"')
    motion.insert_rest_pose()
    return motion


@app.command()
def main(
    # path config
    smplx_path: Annotated[
        Path,
        Argument(
            ...,
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
            help='filepath of the smplx motion (.npz) to be retargeted',
        ),
    ],
    # engine config
    blender_exec: Annotated[
        Path,
        Option('--blender-exec', help='path to blender executable, e.g. /usr/bin/blender'),
    ] = None,
    # misc
    debug: Annotated[
        bool,
        Option('--debug/--no-debug', help='log in debug mode'),
    ] = False,
):
    """Visualize a SMPL-X motion with a command line interface."""
    logger = setup_logger(level='DEBUG' if debug else 'INFO')
    logger.info(
        dedent(
            f"""\
            :rocket: Starting:
            Executing install plugin with the following parameters:
            ---------------------------------------------------------
            [yellow]# path config[/yellow]
            - smplx_path: {smplx_path}
            [yellow]# engine config[/yellow]
            - blender_exec: {blender_exec}
            [yellow]# misc[/yellow]
            - debug: {debug}
            ---------------------------------------------------------"""
        )
    )

    with xf.init_blender(exec_path=blender_exec, background=True) as xf_runner:
        logger.info(f'Loading motion data: {smplx_path} ...')
        motion = read_smpl_x(smplx_path)

        logger.info('Adding smplx actor using smplx_addon ...')
        smplx_rig_name = add_smplx()

        logger.info('Applying motion data to actor ...')
        xf_runner.utils.apply_motion_data_to_actor(motion_data=motion.get_motion_data(), actor_name=smplx_rig_name)
        xf_runner.utils.set_frame_range(start=0, end=motion.n_frames)

        blend_file = smplx_path.with_name(f'{smplx_path.stem}.blend')
        logger.info(f'Saving it to blend file "{blend_file}" ...')
        xf_runner.utils.save_blend(blend_file)

    logger.info(':tada: [green]Visualization finished[/green]!')


if __name__ == '__main__':
    app()
