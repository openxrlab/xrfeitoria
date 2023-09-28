"""Utils for load images and annotations.

Requirements:

```
pip install numpy imath openexr flow_vis opencv-python
```

If you encounter any problems with openexr installation,
refer to the following link:
https://github.com/AcademySoftwareFoundation/openexr/blob/main/INSTALL.md
"""
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np

import os

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

import cv2

try:
    import flow_vis
except ImportError:
    print('warning: please install flow_vis' ' in order to visualize optical flows.')

PathLike = Union[str, Path]


class ExrReader:
    """Utils for exr format data. Load `.exr` format file.

    Requirements: requirements/synbody.txt

    If you encounter any problems with openexr installation,
    refer to the following link:
    https://github.com/AcademySoftwareFoundation/openexr/blob/main/INSTALL.md
    """

    def __init__(self, exr_path: Union[str, Path]):
        """Initialize with a `.exr` format file.

        Args:
            exr_path (PathLike): path to `.exr` format file
        """
        if isinstance(exr_path, Path):
            exr_path = exr_path.as_posix()
        exr_mat = cv2.imread(exr_path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        exr_mat = cv2.cvtColor(exr_mat, cv2.COLOR_BGR2RGB)
        self.exr_mat = exr_mat

    @staticmethod
    def float2int(array: np.ndarray) -> np.ndarray:
        """Convert ndarray to uint8 that can be display as image. Values greater than
        255 will be clipped.

        Args:
            array (np.ndarray): input ndarray

        Returns:
            np.ndarray: array of dtype=unit8
        """
        array = np.round(array * 255)
        array = np.clip(array, 0, 255)
        return array.astype(np.uint8)

    def get_rgb(self) -> np.ndarray:
        """Get RGB channel in `.exr` format.

        Returns:
            np.ndarray: masks of shape (H, W, 3)
        """
        rgb = self.exr_mat
        img = self.float2int(rgb)
        return img

    def get_flow(self) -> np.ndarray:
        """Get optical flow in `.exr` format.

        Returns:
            np.ndarray: optical flow data of (H, W, 3) converted to colors
        """
        flow = self.exr_mat[..., :2]
        img = flow_vis.flow_to_color(flow, convert_to_bgr=False)
        return img

    def get_depth(self, depth_rescale: float = 1.0) -> np.ndarray:
        """Get depth in `.exr` format.

        Args:
            depth_rescale (float, optional): scaling the depth
                to map it into (0, 255). Depth values great than
                `depth_rescale` will be clipped. Defaults to 1.0.

        Returns:
            np.ndarray: depth data of shape (H, W, 3)
        """
        depth = self.exr_mat
        img = self.float2int(depth / depth_rescale)
        img[img == 0] = 255
        return img


class XRFeitoriaReader:
    # folder names of each data modal
    MASK = 'mask'
    DEPTH = 'depth'
    OPTICAL_FLOW = 'flow'
    IMG = 'img'
    NORMAL = 'normal'
    DIFFUSE = 'diffuse'

    def __init__(self, sequence_dir: PathLike) -> None:
        self.sequence_dir = Path(sequence_dir)

    def get_img(self, camera_name: str, frame: int) -> np.ndarray:
        """Get rgb image of the given frame ('img/{frame:04d}.*')

        Args:
            camera_name (str): the camera name
            frame (int): the frame number

        Returns:
            np.ndarray: image of shape (H, W, 3)
        """
        folder = self.sequence_dir / self.IMG / camera_name
        if not folder.exists():
            raise ValueError(f'Folder of rgb images not found: {folder}')
        file_path = next(folder.glob(f'{frame:04d}.*')).resolve()
        if not file_path.exists():
            raise ValueError(f'Image of {frame}-frame not found: {file_path}')
        if file_path.suffix == '.exr':
            return ExrReader(file_path).get_rgb()
        else:
            img = cv2.imread(str(file_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img

    def get_diffuse(self, camera_name: str, frame: int) -> np.ndarray:
        """Get diffuse image of the given frame ('diffuse/{frame:04d}.*')

        Args:
            camera_name (str): the camera name
            frame (int): the frame number

        Returns:
            np.ndarray: image of shape (H, W, 3)
        """
        folder = self.sequence_dir / self.DIFFUSE / camera_name
        if not folder.exists():
            raise ValueError(f'Folder of diffuse images not found: {folder}')
        file_path = next(folder.glob(f'{frame:04d}.*')).resolve()
        if not file_path.exists():
            raise ValueError(f'Diffuse image of {frame}-frame not found: {file_path}')
        if file_path.suffix == '.exr':
            return ExrReader(file_path).get_rgb()
        else:
            img = cv2.imread(str(file_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img

    def get_mask(self, camera_name: str, frame: int) -> np.ndarray:
        """Get mask of the given frame ('mask/{frame:04d}.*')

        Args:
            camera_name (str): the camera name
            frame (int): the frame number

        Returns:
            np.ndarray: image of shape (H, W, 3)
        """
        folder = self.sequence_dir / self.MASK / camera_name
        if not folder.exists():
            raise ValueError(f'Folder of masks not found: {folder}')
        file_path = next(folder.glob(f'{frame:04d}.*')).resolve()
        if not file_path.exists():
            raise ValueError(f'Mask of {frame}-frame not found: {file_path}')
        if file_path.suffix == '.exr':
            return ExrReader(file_path).get_rgb()
        else:
            img = cv2.imread(str(file_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img

    def get_depth(self, camera_name: str, frame: int, depth_rescale=1.0) -> np.ndarray:
        """Get depth of the given frame ('depth/{frame:04d}.*')

        Args:
            camera_name (str): the camera name
            frame (int): the frame number
            depth_rescale (float, optional): scaling the depth
                to map it into (0, 255). Depth values great than
                `depth_rescale` will be clipped. Defaults to 1.0.

        Returns:
            np.ndarray: depth of shape (H, W, 3)
        """
        folder = self.sequence_dir / self.DEPTH / camera_name
        if not folder.exists():
            raise ValueError(f'Folder of depth not found: {folder}')
        file_path = next(folder.glob(f'{frame:04d}.*')).resolve()
        if not file_path.exists():
            raise ValueError(f'Depth of {frame}-frame not found: {file_path}')
        if file_path.suffix == '.exr':
            return ExrReader(file_path).get_depth(depth_rescale=depth_rescale)
        else:
            img = cv2.imread(str(file_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img

    def get_flow(self, camera_name: str, frame: int) -> np.ndarray:
        """Get optical flow of the given frame ('flow/{frame:04d}.*')

        Args:
            camera_name (str): the camera name
            frame (int): the frame number
            depth_rescale (float, optional): scaling the depth
                to map it into (0, 255). Depth values great than
                `depth_rescale` will be clipped. Defaults to 1.0.

        Returns:
            np.ndarray: optical flow of shape (H, W, 3)
        """
        folder = self.sequence_dir / self.OPTICAL_FLOW / camera_name
        if not folder.exists():
            raise ValueError(f'Folder of depth not found: {folder}')
        file_path = next(folder.glob(f'{frame:04d}.*')).resolve()
        if not file_path.exists():
            raise ValueError(f'Depth of {frame}-frame not found: {file_path}')
        if file_path.suffix == '.exr':
            return ExrReader(file_path).get_flow()
        else:
            img = cv2.imread(str(file_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img

    def get_normal(self, camera_name: str, frame: int) -> np.ndarray:
        """Get normal map of the given frame ('normal/{frame:04d}.*')

        Args:
            camera_name (str): the camera name
            frame (int): the frame number

        Returns:
            np.ndarray: normal map of shape (H, W, 3)
        """
        folder = self.sequence_dir / self.NORMAL / camera_name
        if not folder.exists():
            raise ValueError(f'Folder of normal mpa not found: {folder}')
        file_path = next(folder.glob(f'{frame:04d}.*')).resolve()
        if not file_path.exists():
            raise ValueError(f'Normal map of {frame}-frame not found: {file_path}')
        if file_path.suffix == '.exr':
            return ExrReader(file_path).get_rgb()
        else:
            img = cv2.imread(str(file_path))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return img
