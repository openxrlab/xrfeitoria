from typing import ContextManager, List, Optional, Union

from typing_extensions import deprecated

from ..data_structure.constants import default_level_blender
from .sequence_blender import SequenceBlender as SequenceBlender
from .sequence_unreal import SequenceUnreal as SequenceUnreal

@deprecated('Use `xf_runner.sequence` function instead.', category=DeprecationWarning)
class SequenceWrapperBlender:
    @deprecated('This class is deprecated, use `xf_runner.sequence` function instead.', category=DeprecationWarning)
    @classmethod
    def new(
        cls, seq_name: str, level: str = ..., seq_fps: int = ..., seq_length: int = ..., replace: bool = ...
    ) -> ContextManager[SequenceBlender]: ...
    @deprecated('This class is deprecated, use `xf_runner.sequence` function instead.', category=DeprecationWarning)
    @classmethod
    def open(cls, seq_name: str) -> ContextManager[SequenceBlender]: ...

@deprecated('Use `xf_runner.sequence` function instead.', category=DeprecationWarning)
class SequenceWrapperUnreal:
    @deprecated('This class is deprecated, use `xf_runner.sequence` function instead.', category=DeprecationWarning)
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
    @deprecated('This class is deprecated, use `xf_runner.sequence` function instead.', category=DeprecationWarning)
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
