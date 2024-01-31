import os
import time
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import List

import numpy as np
from loguru import logger

import xrfeitoria as xf
from xrfeitoria.camera.camera_parameter import CameraParameter
from xrfeitoria.utils import projector
from xrfeitoria.utils import setup_logger as _setup_logger

try:
    from .config import blender_exec, unreal_exec, unreal_project
except ModuleNotFoundError:
    logger.error('config.py file not found. Run `python -m samples.setup` or `python -m tests.setup` to create it.')
    raise SystemExit(1)


def visualize_vertices(camera_name, actor_names: List[str], seq_output_path: Path, frame_idx=0):
    """Visualize vertices in the first frame of the first sequence.

    Args:
        camera_name (str): camera name
        actor_names (List[str]): actor names
        seq_name (str, optional): sequence name. Defaults to {seq_name}
    """
    # TODO: move to utils.viewer
    try:
        from PIL import Image
    except ImportError:
        logger.error('[red]Please install "Pillow" to visualize vertices:[/red] [bold]pip install Pillow[/bold]')
        exit(1)

    logger.info('Visualizing vertices')
    # fixed file structure
    img_path = seq_output_path / 'img' / camera_name / f'{frame_idx:04d}.png'
    camera_param_json = seq_output_path / 'camera_params' / camera_name / f'{frame_idx:04d}.json'

    # load img and camera parameters
    img = np.array(Image.open(img_path.as_posix()))
    camera_param = CameraParameter.fromfile(camera_param_json.as_posix())

    # load and draw vertices looping over actors
    vis_dir = seq_output_path / 'vertices_vis'
    vis_dir.mkdir(exist_ok=True, parents=True)
    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
    ]
    for idx, actor_name in enumerate(actor_names):
        vert_path = seq_output_path / 'vertices' / f'{actor_name}.npz'
        verts = np.load(vert_path, allow_pickle=True)['verts']
        # draw vertices on image
        img = projector.draw_points3d(verts[frame_idx], camera_param, image=img, color=colors[idx])

    save_path = vis_dir / f'{frame_idx:04d}-overlap.png'
    Image.fromarray(img).save(save_path.as_posix())
    logger.info(f'Original image: "{img_path.as_posix()}"')
    logger.info(f'Overlap image saved to: "{save_path.as_posix()}"')


@contextmanager
def __timer__(step_name: str):
    t1 = time.time()
    yield
    t2 = time.time()
    logger.info(f'⌛ {step_name} executed in {(t2-t1):.4f} s')


def parse_args():
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--engine', '-e', choices=['unreal', 'blender'], default='unreal', help='engine to run')
    args.add_argument('--debug', action='store_true', help='log debug info')
    args.add_argument('--background', '-b', action='store_true', help='run in background')
    args = args.parse_args()
    return args


_init_blender = partial(
    xf.init_blender,
    exec_path=blender_exec,
    new_process=False,
    replace_plugin=False,
    dev_plugin=False,
)
_init_unreal = partial(
    xf.init_unreal,
    exec_path=unreal_exec,
    project_path=unreal_project,
    new_process=False,
    replace_plugin=False,
    dev_plugin=False,
)
