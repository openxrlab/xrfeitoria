from pathlib import Path

import cv2
import numpy as np

from xrfeitoria.camera.camera_parameter import CameraParameter
from xrfeitoria.utils import projector

root = Path(__file__).parent


def test_blender():
    output_root = root.parent.parent / 'samples' / 'blender' / 'output'
    seq_root = output_root / '03_basic_usage'
    camera_name = 'level_camera'
    img_path = seq_root / 'img' / camera_name / '0000.png'
    verts_path = seq_root / 'verts' / 'SMPLX-mesh-neutral.npz'
    img = cv2.imread(str(img_path))
    verts = np.load(str(verts_path), allow_pickle=True)['verts']
    camera_param_json = seq_root / 'camera_param' / f'{camera_name}.json'

    camera_param = CameraParameter.fromfile(camera_param_json.as_posix())
    overlap_img = projector.draw_points3d(verts[0], camera_param, image=img, color=(0, 255, 255))
    cv2.imwrite(str(root / 'overlap.png'), overlap_img)
    print(f'Overlap image saved to: "{root / "overlap.png"}"')


def test_unreal():
    output_root = root.parent / 'unreal' / 'output'
    seq_root = output_root / 'test'
    camera_name = 'Camera'
    img_path = seq_root / 'img' / camera_name / '0000.png'
    verts_path = seq_root / 'vertices' / 'Actor_4.npz'
    img = cv2.imread(str(img_path))
    verts = np.load(str(verts_path), allow_pickle=True)['verts']
    camera_param_json = seq_root / 'camera_params' / f'{camera_name}Actor1.json'
    camera_param = CameraParameter.fromfile(camera_param_json.as_posix())
    overlap_img = projector.draw_points3d(verts[0], camera_param, image=img, color=(0, 255, 255))
    cv2.imwrite(str(root / 'overlap.png'), overlap_img)
    print(f'Overlap image saved to: "{root / "overlap.png"}"')


if __name__ == '__main__':
    # test_blender()
    test_unreal()
