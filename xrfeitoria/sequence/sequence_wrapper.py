"""Sequence wrapper functions."""

import warnings
from contextlib import contextmanager
from typing import ContextManager, List, Optional, Tuple, Union

from typing_extensions import deprecated

from ..data_structure.constants import default_level_blender
from ..utils.functions import blender_functions, unreal_functions
from .sequence_base import SequenceBase
from .sequence_blender import SequenceBlender
from .sequence_unreal import SequenceUnreal

__all__ = ['sequence_wrapper_blender', 'sequence_wrapper_unreal']


@deprecated('Use `xf_runner.sequence` function instead.', category=DeprecationWarning)
class SequenceWrapperBlender:
    """Sequence utils class."""

    _seq = SequenceBlender
    _warn_msg = (
        '\n`Sequence` class will be deprecated in the future. Please use `sequence` function instead:\n'
        '>>> xf_runner = xf.init_blender()\n'
        '>>> with xf_runner.sequence(...) as seq: ...'
    )

    @classmethod
    @contextmanager
    def new(
        cls,
        seq_name: str,
        level: str = default_level_blender,
        seq_fps: int = 30,
        seq_length: int = 1,
        replace: bool = False,
    ) -> ContextManager[SequenceBase]:
        """Create a new sequence and close the sequence after exiting the it.

        Args:
            seq_name (str): Name of the sequence.
            level (str, optional): Name of the level. Defaults to None.
            seq_fps (int, optional): Frame per second of the new sequence. Defaults to 30.
            seq_length (int, optional): Frame length of the new sequence. Defaults to 1.
            replace (bool, optional): Replace the exist same-name sequence. Defaults to False.
        Yields:
            SequenceBase: Sequence object.
        """
        warnings.showwarning(cls._warn_msg, DeprecationWarning, __file__, 0)
        cls._seq._new(
            seq_name=seq_name,
            level=level,
            seq_fps=seq_fps,
            seq_length=seq_length,
            replace=replace,
        )
        yield cls._seq
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
        warnings.showwarning(cls._warn_msg, DeprecationWarning, __file__, 0)
        cls._seq._open(seq_name=seq_name)
        yield cls._seq
        cls._seq.close()


@deprecated('Use `xf_runner.sequence` function instead.', category=DeprecationWarning)
class SequenceWrapperUnreal:
    """Sequence utils class for Unreal."""

    _seq = SequenceUnreal
    _warn_msg = (
        '\n`Sequence` class will be deprecated in the future. Please use `sequence` function instead:\n'
        '>>> xf_runner = xf.init_unreal()\n'
        '>>> with xf_runner.sequence(...) as seq: ...'
    )

    @classmethod
    @contextmanager
    def open(cls, seq_name: str, seq_dir: 'Optional[str]' = None) -> ContextManager[SequenceUnreal]:
        """Open a sequence and close the sequence after existing it.

        Args:
            seq_name (str): Name of the sequence.
            seq_dir (Optional[str], optional): Path of the sequence.
                Defaults to None and fallback to the default path '/Game/XRFeitoriaUnreal/Sequences'.

        Yields:
            SequenceUnreal: Sequence object.
        """
        cls._seq._open(seq_name=seq_name, seq_dir=seq_dir)
        cls._seq.show()
        yield cls._seq
        cls._seq.save()
        cls._seq.close()

    @classmethod
    @contextmanager
    def new(
        cls,
        seq_name: str,
        level: 'Optional[str]' = None,
        seq_fps: 'Optional[float]' = 30,
        seq_length: 'Optional[int]' = 1,
        replace: bool = False,
        seq_dir: 'Optional[str]' = None,
    ) -> ContextManager[SequenceUnreal]:
        """Create a new sequence and close the sequence after exiting the it.

        Args:
            seq_name (str): Name of the sequence.
            level (Optional[str], optional): Path of the level in the unreal project. e.g. '/Game/DefaultLevel'.
                Defaults to None. If None, use the current level.
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
        cls._seq.show()
        yield cls._seq
        cls._seq.save()
        cls._seq.close()


def sequence_wrapper_blender(
    seq_name: str,
    level: str = default_level_blender,
    seq_fps: int = 30,
    seq_length: int = 1,
    replace: bool = False,
) -> Union[SequenceBlender, ContextManager[SequenceBlender]]:
    """Create a new sequence and close the sequence after exiting it.

    Args:
        seq_name (str): The name of the sequence.
        level (str, optional): The level to associate the sequence with. Defaults to 'XRFeitoria'.
        seq_fps (int, optional): The frames per second of the sequence. Defaults to 30.
        seq_length (int, optional): The length of the sequence. Defaults to 1.
        replace (bool, optional): Whether to replace an existing sequence with the same name. Defaults to False.

    Returns:
        SequenceBlender: The created SequenceBlender object.
    """
    if blender_functions.check_sequence(seq_name=seq_name) and not replace:
        SequenceBlender._open(seq_name=seq_name)
    else:
        SequenceBlender._new(seq_name=seq_name, level=level, seq_fps=seq_fps, seq_length=seq_length, replace=replace)
    return SequenceBlender()


def sequence_wrapper_unreal(
    seq_name: str,
    seq_dir: Optional[str] = None,
    level: Optional[str] = None,
    seq_fps: int = 30,
    seq_length: int = 1,
    replace: bool = False,
) -> Union[SequenceUnreal, ContextManager[SequenceUnreal]]:
    """Create a new sequence, open it in editor, and close the sequence after exiting
    it.

    Args:
        seq_name (str): The name of the sequence.
        seq_dir (Optional[str], optional): The directory where the sequence is located. Defaults to None. Falls back to the default sequence path (/Game/XRFeitoriaUnreal/Sequences).
        level (Optional[str], optional): The level to associate the sequence with. Defaults to None.
        seq_fps (int, optional): The frames per second of the sequence. Defaults to 30.
        seq_length (int, optional): The length of the sequence in frames. Defaults to 1.
        replace (bool, optional): Whether to replace an existing sequence with the same name. Defaults to False.

    Returns:
        SequenceUnreal: The created SequenceUnreal object.
    """

    default_sequence_dir = SequenceUnreal._get_default_seq_dir_in_engine()
    seq_dir = seq_dir or default_sequence_dir
    if (
        unreal_functions.check_asset_in_engine(f'{seq_dir}/{seq_name}')
        and unreal_functions.check_asset_in_engine(f'{seq_dir}/{seq_name}_data')
        and not replace
    ):
        SequenceUnreal._open(seq_name=seq_name, seq_dir=seq_dir)
    else:
        SequenceUnreal._new(
            seq_name=seq_name,
            seq_dir=seq_dir,
            level=level,
            seq_fps=seq_fps,
            seq_length=seq_length,
            replace=replace,
        )
    # Open the sequence in editor, for letting `get_bound_objects` work
    SequenceUnreal.show()
    return SequenceUnreal()
