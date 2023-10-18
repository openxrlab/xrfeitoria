from typing import Optional, Tuple

import numpy as np
import numpy.typing as npt
from scipy.spatial.transform import Rotation as spRotation
from typing_extensions import Self


class Matrix:
    """2D matrix, support matrix multiplication."""

    __slots__ = ("data",)

    def __init__(self, mat: Optional[npt.ArrayLike] = None):
        if mat is None:
            mat = np.eye(4, dtype=np.float64)
        else:
            mat = np.array(mat, dtype=np.float64)
            if not (mat.ndim == 2 and 2 <= mat.shape[0] <= 4 and 2 <= mat.shape[1] <= 4):
                raise TypeError(
                    "Matrix(): expects no args or a single arg containing 2-4"
                    f" numeric sequences. Got shape: {mat.shape}"
                )
        self.data = mat

    def to_4x4(self) -> Self:
        mat = np.eye(4)
        old = self.data[:4, :4]
        mat[: old.shape[0], : old.shape[1]] = old
        return Matrix(mat)

    def to_3x3(self) -> Self:
        mat = np.eye(3)
        old = self.data[:3, :3]
        mat[: old.shape[0], : old.shape[1]] = old
        return Matrix(mat)

    def to_2x2(self) -> Self:
        mat = np.eye(2)
        old = self.data[:2, :2]
        mat[: old.shape[0], : old.shape[1]] = old
        return Matrix(mat)

    def inverted(self) -> Self:
        return Matrix(np.linalg.inv(self.data))

    def decompose(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return decompose_trs(self.to_4x4())

    @staticmethod
    def _to_matmul_type(value) -> np.ndarray:
        if isinstance(value, (Matrix, Vector)):
            return value.data
        try:
            return np.array(value)
        except Exception as e:
            raise TypeError(f"Unsupported operand type for @, value: {value}")

    def __matmul__(self, other) -> Self:
        right = self._to_matmul_type(other)
        left = self.data
        if self.data.shape[1] != other.data.shape[0]:
            raise ValueError("Matrix multiplication: shape mismatch: " f"{left.shape} @ {right.shape}")
        return Matrix(left @ right)

    def __rmatmul__(self, other) -> Self:
        left = self._to_matmul_type(other)
        right = self.data
        if self.data.shape[1] != other.data.shape[0]:
            raise ValueError("Matrix multiplication: shape mismatch: " f"{left.shape} @ {right.shape}")
        return Matrix(left @ right)

    @property
    def shape(self):
        return self.data.shape

    def __array__(self):
        return self.data

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self) -> str:
        return f"Matrix({self.data.tolist()})"

    def __repr__(self) -> str:
        text = f"Matrix({tuple(self.data[0, :].tolist())},"
        for i in range(1, self.data.shape[0] - 1):
            text += f"\n        {tuple(self.data[i, :].tolist())},"
        text += f"\n        {tuple(self.data[-1, :].tolist())})"
        return text


class Vector:
    """1D vector"""

    __slots__ = ("data",)

    def __init__(self, vector: Optional[npt.ArrayLike] = None):
        if vector is None:
            vector = np.zeros(3, dtype=np.float64)
        else:
            vector = np.array(vector, dtype=np.float64)
            if not (vector.ndim == 1 and vector.shape[0] >= 2):
                raise ValueError("Vector(): expected 1D numeric sequence of size >= 2." f" Got shape: {vector.shape}")

        self.data = np.array(vector, dtype=np.float64)

    @property
    def x(self) -> float:
        return self.data[0]

    @property
    def y(self) -> float:
        return self.data[1]

    @property
    def z(self) -> float:
        return self.data[2] if self.data.shape[0] > 2 else 0.0

    @property
    def w(self) -> float:
        return self.data[3] if self.data.shape[0] > 3 else 0.0

    @property
    def shape(self):
        return self.data.shape

    def __array__(self):
        return self.data

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self) -> str:
        return f"Vector({tuple(self.data.tolist())})"

    def __repr__(self) -> str:
        return self.__str__()


def decompose_trs(
    mat: npt.ArrayLike,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decompose a 4x4 transformation matrix into 3 parts:
    translation, rotation, scale.

    Parameters
    ----------
    mat : npt.ArrayLike
        A transformation matrix of shape (N, 4, 4) or (4, 4)
        e.g.
            [
                [1, 0, 0, x],
                [0, 1, 0, y],
                [0, 0, 1, z],
                [0, 0, 0, 1],
            ]

    Returns
    -------
    Tuple[np.ndarray, np.ndarray, np.ndarray]
        - translation(x, y, z): np.ndarray of shape (N, 3) or (3,)
        - quaternion(w, x, y, z): np.ndarray of shape (N, 4)
        - scaling(x, y, z): np.ndarray of shape (N, 3) or (3,)
    """
    mat = np.array(mat)
    ndim = mat.ndim
    if ndim == 2:
        mat = mat[np.newaxis, ...]
        unsqueeze = True
    elif ndim == 3:
        unsqueeze = False
    else:
        raise ValueError(f"mat must be 2d or 3d array. Got shape: {mat.shape}")

    transl = mat[:, :3, 3]
    mat_nx3x3 = mat[:, :3, :3]
    scale = np.linalg.norm(mat_nx3x3, axis=1).reshape(-1, 3)
    if unsqueeze:
        transl = transl.squeeze(0)
        scale = scale.squeeze(0)

    r_mat = mat_nx3x3 / scale[:, np.newaxis]
    quat = spRotation.from_matrix(r_mat).as_quat()
    quat = quat[0, [3, 0, 1, 2]]
    return transl, quat, scale
