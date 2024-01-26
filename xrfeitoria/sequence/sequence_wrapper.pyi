from typing import ContextManager, List, Optional, Union

from ..data_structure.constants import default_level_blender
from .sequence_blender import SequenceBlender as SequenceBlender
from .sequence_unreal import SequenceUnreal as SequenceUnreal

class SequenceWrapperBlender:
    @classmethod
    def new(
        cls, seq_name: str, level: str = ..., seq_fps: int = ..., seq_length: int = ..., replace: bool = ...
    ) -> ContextManager[SequenceBlender]: ...
    @classmethod
    def open(cls, seq_name: str) -> ContextManager[SequenceBlender]: ...

class SequenceWrapperUnreal:
    @classmethod
    def new(
        cls,
        seq_name: str,
        level: str = ...,
        seq_fps: Optional[float] = ...,
        seq_length: Optional[int] = ...,
        replace: bool = ...,
        seq_dir: Optional[str] = ...,
    ) -> ContextManager[SequenceUnreal]: ...
    @classmethod
    def open(cls, seq_name: str, seq_dir: Optional[str] = ...) -> ContextManager[SequenceUnreal]: ...

def sequence_wrapper_blender(
    seq_name: str,
    level: str = default_level_blender,
    seq_fps: int = 30,
    seq_length: int = 1,
    replace: bool = False,
) -> Union[SequenceBlender, ContextManager[SequenceBlender]]: ...
def sequence_wrapper_unreal(
    seq_name: str,
    seq_dir: Optional[str] = None,
    level: Optional[str] = None,
    seq_fps: int = 30,
    seq_length: int = 1,
    replace: bool = False,
) -> Union[SequenceUnreal, ContextManager[SequenceUnreal]]: ...
