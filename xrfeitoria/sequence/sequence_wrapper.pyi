from typing import ContextManager, List, Optional, Union

from .sequence_blender import SequenceBlender as SequenceBlender
from .sequence_unreal import SequenceUnreal as SequenceUnreal

class SequenceWrapperBase:
    @classmethod
    def new(
        cls,
        seq_name: str,
        level: Union[str, List[str]] = ...,
        seq_fps: int = ...,
        seq_length: int = ...,
        replace: bool = ...,
    ) -> ...: ...
    @classmethod
    def open(cls, seq_name: str) -> ...: ...

class SequenceWrapperBlender(SequenceWrapperBase):
    @classmethod
    def new(
        cls,
        seq_name: str,
        level: Union[str, List[str]] = ...,
        seq_fps: int = ...,
        seq_length: int = ...,
        replace: bool = ...,
    ) -> ContextManager[SequenceBlender]:
        """Create a new sequence and close the sequence after exiting the it.

        Args:
            seq_name (str): Name of the sequence.
            level (Union[str, List[str]], optional): Name of the level. Defaults to [].
            seq_fps (int, optional): Frame per second of the new sequence. Defaults to 60.
            seq_length (int, optional): Frame length of the new sequence. Defaults to 60.
            replace (bool, optional): Replace the exist same-name sequence. Defaults to False.
        Yields:
            SequenceBlender: Sequence object.
        """
    @classmethod
    def open(cls, seq_name: str) -> ContextManager[SequenceBlender]: ...

class SequenceWrapperUnreal(SequenceWrapperBase):
    @classmethod
    def new(
        cls,
        seq_name: str,
        level: str,
        seq_fps: Optional[float] = ...,
        seq_length: Optional[int] = ...,
        replace: bool = ...,
        seq_dir: Optional[str] = ...,
    ) -> ContextManager[SequenceUnreal]: ...
    @classmethod
    def open(cls, seq_name: str) -> ContextManager[SequenceUnreal]: ...
