"""Project 3D points to 2D points, and draw 3D points on image, using XRPrimer
camera."""


from typing import Optional, Tuple, Union

import numpy as np

from ..camera.camera_parameter import CameraParameter


def project_points3d(points3d: np.ndarray, camera_param: CameraParameter) -> np.ndarray:
    """Project 3D point to 2D point.

    Args:
        point3d (np.ndarray): [N, 3] points to project, where N is the number of points,
            and 3 is the location of each point. In convention of 'opencv'.
        camera_param (PinholeCameraParameter): camera parameter in convention of xrprimer

    Returns:
        np.ndarray: [N, 2] projected 2d points, dtype=np.float32
    """
    points3d = np.concatenate([points3d, np.ones((points3d.shape[0], 1))], axis=1)  # [N, 4]

    # convert to opencv convention, and cam2world
    _camera_param = camera_param.clone()
    if _camera_param.world2cam:
        _camera_param.inverse_extrinsic()
    if _camera_param.convention != 'opencv':
        _camera_param.convert_convention(dst='opencv')
    point2d = _camera_param.projection_matrix @ points3d.T  # [3, N]
    point2d = point2d[:2] / point2d[2]  # [2, N]
    return point2d.T


def points2d_to_canvas(points2d: np.ndarray, resolution: Tuple[int, int]) -> np.ndarray:
    """Draw 2d points on canvas. The canvas is a binary image, where 1 means the points
    are drawn.

    Args:
        points2d (np.ndarray): [N, 2] points to draw
        resolution (Tuple[int, int]): [height, width] of the canvas

    Returns:
        np.ndarray: [height, width] binary image, where 1 means the points are drawn, dtype=np.bool
    """
    height, width = resolution
    x = points2d[:, 1].astype('int').clip(0, height - 1)
    y = points2d[:, 0].astype('int').clip(0, width - 1)
    canvas = np.zeros((height, width), dtype=bool)
    canvas[x, y] = True
    return canvas


def draw_points3d(
    points3d: np.ndarray,
    camera_param: CameraParameter,
    image: Optional[np.ndarray] = None,
    color: Tuple[int, int, int] = (255, 0, 0),
) -> np.ndarray:
    """Draw 3d points on canvas. The 3d points will be projected to 2d points first.
    Then draw the 2d points on a canvas of the same size as the image. If image is not
    None, the canvas will be drawn on the image. Otherwise, the canvas will be returned
    which is a binary image, where 1 means the points are drawn.

    Args:
        point3d (np.ndarray): [N, 3] points to project, where N is the number of points,
            and 3 is the location of each point. In convention of opencv.
        camera_param (PinholeCameraParameter): camera parameter
        image (Optional[np.ndarray], optional): [height, width, channel]. Defaults to None.
            If not None, the canvas will be drawn on the image with the given color.
        color (Tuple[int, int, int], optional): color of the points. Defaults to (255, 0, 0).

    Returns:
        np.ndarray:
            If image is None, return a binary image [H, W], where 1 means the points are drawn, dtype=np.bool.
            Otherwise, return a image [H, W, C] with the points drawn on it, dtype=np.uint8.
    """
    points2d = project_points3d(points3d, camera_param)
    canvas = points2d_to_canvas(points2d, [camera_param.height, camera_param.width])
    if image is not None:
        if image.shape[-1] == 4:
            color += (255,)
        elif image.shape[-1] == 1:
            color = (color[0],)
        image[canvas] = color
        return image
    return canvas
