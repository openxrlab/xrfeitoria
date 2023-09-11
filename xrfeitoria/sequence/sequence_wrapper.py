from contextlib import contextmanager
from typing import ContextManager, List, Optional, Tuple, Union

from .sequence_base import SequenceBase
from .sequence_blender import SequenceBlender
from .sequence_unreal import SequenceUnreal


class SequenceWrapperBase:
    """Sequence utils class."""

    _seq = SequenceBase

    @classmethod
    @contextmanager
    def new(
        cls,
        seq_name: str,
        level: Union[str, List[str]] = [],
        seq_fps: int = 30,
        seq_length: int = 1,
        replace: bool = False,
    ) -> ContextManager[SequenceBase]:
        """Create a new sequence and close the sequence after exiting the it.

        Args:
            seq_name (str): Name of the sequence.
            level (Union[str, List[str]], optional): Name of the level. Defaults to [].
            seq_fps (int, optional): Frame per second of the new sequence. Defaults to 30.
            seq_length (int, optional): Frame length of the new sequence. Defaults to 1.
            replace (bool, optional): Replace the exist same-name sequence. Defaults to False.
        Yields:
            SequenceBase: Sequence object.
        """
        cls._seq._new(
            seq_name=seq_name,
            level=level,
            seq_fps=seq_fps,
            seq_length=seq_length,
            replace=replace,
        )
        yield cls._seq
        cls._seq.save()
        cls._seq.close()

    @classmethod
    @contextmanager
    def open(cls, seq_name: str) -> ContextManager[SequenceBase]:
        """Open a sequence and close the sequence after existing it.

        Args:
            seq_name (str): Name of the sequence.

        Yields:
            SequenceBase: Sequence object.
        """
        cls._seq._open(seq_name=seq_name)
        yield cls._seq
        cls._seq.save()
        cls._seq.close()


class SequenceWrapperBlender(SequenceWrapperBase):
    """Sequence utils class for Blender."""

    _seq = SequenceBlender


class SequenceWrapperUnreal(SequenceWrapperBase):
    """Sequence utils class for Unreal."""

    _seq = SequenceUnreal

    @classmethod
    @contextmanager
    def new(
        cls,
        seq_name: str,
        level: str,
        seq_fps: 'Optional[float]' = 30,
        seq_length: 'Optional[int]' = 1,
        replace: bool = False,
        seq_dir: 'Optional[str]' = None,
    ) -> ContextManager[SequenceUnreal]:
        """Create a new sequence and close the sequence after exiting the it.

        Args:
            seq_name (str): Name of the sequence.
            level (str): Path of the level in the unreal project. e.g. '/Game/DefaultLevel'.
            seq_fps (Optional[float], optional): Frame per second of the new sequence. Defaults to 30.
            seq_length (Optional[int], optional): Frame length of the new sequence. Defaults to 1.
            replace (bool, optional): Replace the exist same-name sequence. Defaults to False.
            seq_dir (Optional[str], optional): Path of the sequence.
                Defaults to None and fallback to the default path '/Game/XRFeitoriaUnreal/Sequences'.
        Yields:
            SequenceUnreal: Sequence object.
        """
        cls._seq._new(
            seq_name=seq_name,
            level=level,
            seq_fps=seq_fps,
            seq_length=seq_length,
            replace=replace,
            seq_dir=seq_dir,
        )
        yield cls._seq
        cls._seq.save()
        cls._seq.close()
