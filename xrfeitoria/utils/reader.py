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
from PIL import Image
from xrprimer.data_structure.camera import PinholeCameraParameter

try:
    import flow_vis
except ImportError:
    print('warning: please install flow_vis' ' in order to visualize optical flows.')

try:
    import Imath
    import OpenEXR

    has_exr = True
    import_exception = ''
except (ImportError, ModuleNotFoundError):
    has_exr = False
    import traceback

    stack_str = ''
    for line in traceback.format_stack():
        if 'frozen' not in line:
            stack_str += line + '\n'
    import_exception = traceback.format_exc() + '\n'
    import_exception = stack_str + import_exception

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
        if not has_exr:
            print(import_exception)
            print('warning: please install Imath and OpenEXR' ' in order to read .exr format files.')
            raise ImportError
        file_ = OpenEXR.InputFile(str(exr_path))
        dw = file_.header()['dataWindow']
        size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
        self.file = file_
        self.size: Tuple[int, int] = size

    @property
    def channels(self) -> List[str]:
        """Get channels in the exr file.

        Returns:
            List[str]: list of channel names
        """
        return self.file.header()['channels']

    def read_channel(self, channel: str) -> np.ndarray:
        """Read channel's data.

        Args:
            channel (str): channel's name

        Returns:
            np.ndarray: channel's data in np.ndarray format with shape (H, W)
        """
        ChannelType = self.file.header()['channels'][channel]
        if ChannelType == Imath.Channel(Imath.PixelType(Imath.PixelType.HALF)):
            PixType = Imath.PixelType(Imath.PixelType.HALF)
            dtype = np.float16
        elif ChannelType == Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT)):
            PixType = Imath.PixelType(Imath.PixelType.FLOAT)
            dtype = np.float32
        else:
            raise ValueError('please specify PixelType')

        img = np.frombuffer(self.file.channel(channel, PixType), dtype=dtype)
        img = np.reshape(img, (self.size[1], self.size[0])).astype(np.float32)
        return img

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
        r = self.read_channel('R')
        g = self.read_channel('G')
        b = self.read_channel('B')
        img = np.stack((r, g, b), axis=2)
        img = self.float2int(img)
        return img

    def get_flow(self) -> np.ndarray:
        """Get optical flow in `.exr` format.

        Returns:
            np.ndarray: optical flow data of (H, W, 3) converted to colors
        """
        flow_r = self.read_channel('R')
        flow_g = self.read_channel('G')
        flow = np.stack((flow_r, flow_g), axis=2)
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
        r = self.read_channel('R')
        g = self.read_channel('G')
        b = self.read_channel('B')
        depth = np.stack((r, g, b), axis=2)

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
            img = np.array(Image.open(file_path.as_posix()))
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
            img = np.array(Image.open(file_path.as_posix()))
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
            img = np.array(Image.open(file_path.as_posix()))
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
            img = np.array(Image.open(file_path.as_posix()))
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
            img = np.array(Image.open(file_path.as_posix()))
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
            img = np.array(Image.open(file_path.as_posix()))
            return img
