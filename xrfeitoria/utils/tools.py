"""Utils tools for logging and progress bar."""

import os
import sys
from pathlib import Path
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union

import loguru
from loguru import logger
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    ProgressType,
    Task,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text

from ..data_structure.constants import PathLike

__all__ = ['setup_logger']


class LoggerWrapper:
    """A wrapper for logger tools."""

    is_setup = False
    logger_record = set()
    # ^8 means center align, 8 characters
    logger_format = '{time:YYYY-MM-DD HH:mm:ss} | ' + '{level:^8} | ' + '{message}'

    @staticmethod
    def find_logger_file() -> str:
        """Find the logger file."""
        from loguru._file_sink import FileSink

        for _, _handler in logger._core.handlers.items():
            _sink = _handler._sink
            if isinstance(_sink, FileSink):
                return _sink._path

    @classmethod
    def filter_unique(cls, record: 'loguru.Record', level_name: str = 'WARNING') -> bool:
        """Filter unique warning massage.

        Args:
            record (loguru.Record): Loguru record.
            level_name (str, optional): logging level. Defaults to "WARNING".

        Returns:
            bool: _description_
        """
        msg = record['message']
        level = record['level'].name
        if level != level_name:
            return True

        msg = f'{level}: {msg}'
        if msg not in cls.logger_record:
            cls.logger_record.add(msg)
            return True
        return False

    @classmethod
    def setup_logging(
        cls,
        level: Literal['RPC', 'TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO',
        log_path: 'Optional[PathLike]' = None,
        replace: bool = True,
    ) -> 'loguru.Logger':
        """Setup logging to file and console.

        Args:
            level (Literal['RPC', 'TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'], optional):
                logging level. Defaults to "INFO", find more in https://loguru.readthedocs.io/en/stable/api/logger.html.
            log_path (Path, optional): path to save the log file. Defaults to None.
            replace (bool, optional): replace the log file if exists. Defaults to True.
        """
        if cls.is_setup:
            return logger

        cls.setup_encoding()

        # add custom level called RPC, which is the minimum level
        logger.level('RPC', no=1, color='<white>', icon='📢')

        logger.remove()  # remove default logger
        # logger.add(sink=lambda msg: rprint(msg, end=''), level=level, format=cls.logger_format)
        c = Console(
            width=sys.maxsize,  # disable wrapping
            log_time=False,
            log_path=False,
            log_time_format='',
        )
        logger.add(sink=lambda msg: c.print(msg, end=''), level=level, format=cls.logger_format)
        if log_path:
            # add file logger
            log_path = Path(log_path).resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if replace and log_path.exists():
                log_path.unlink(missing_ok=True)
            _level = 'RPC' if level == 'RPC' else 'TRACE'
            logger.add(log_path, level=_level, filter=cls.filter_unique, format=cls.logger_format, encoding='utf-8')
            logger.info(f'Python Logging to "{log_path.as_posix()}"')
        cls.is_setup = True
        return logger

    @staticmethod
    def setup_encoding(
        encoding: Optional[str] = None,
        errorhandler: Literal['ignore', 'replace', 'backslashreplace', 'xmlcharrefreplace'] = 'backslashreplace',
    ):
        """Modify `PYTHONIOENCODING` to prevent suppress UnicodeEncodeError caused by logging of emojis.
        It will affect the default behavior of `sys.stdin`, `sys.stdout` and `sys.stderr`.
        Ref: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONIOENCODING

        Args:
            errorhandler (Literal['ignore', 'replace', 'backslashreplace', 'xmlcharrefreplace'], optional):
                specify which error handler to handle unsupported characters. 'strict' is forbidden. Defaults to 'replace'.
                Ref to https://docs.python.org/3/library/stdtypes.html#str.encode
        """
        encodingname, _, handler = os.environ.get('PYTHONIOENCODING', '').lower().partition(':')
        encoding = encodingname if encodingname else encoding
        # Set an errorhandler except for "strict"
        if handler in ('ignore', 'replace', 'backslashreplace', 'xmlcharrefreplace'):
            errorhandler = handler
        elif handler in ('', 'strict'):
            print(
                f'PYTHONIOENCODING is going to use "strict" errorhandler, which could raise errors during logging. Reset to "{errorhandler}"',
                file=sys.stderr,
            )
        else:
            print(
                f'PYTHONIOENCODING is set with invalid errorhandler "{handler}". Reset to "{errorhandler}"',
                file=sys.stderr,
            )
        # if not encoding.lower().startswith("utf"):
        os.environ['PYTHONIOENCODING'] = f"{encoding or ''}:{errorhandler}"


def setup_logger(
    level: Literal['RPC', 'TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO',
    log_path: 'Optional[PathLike]' = None,
    replace: bool = True,
) -> 'loguru.Logger':
    """Setup logging to file and console.

    Args:
        level (Literal['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'], optional): logging level.
            Defaults to 'INFO', find more in https://loguru.readthedocs.io/en/stable/api/logger.html.
            The order of the levels is:

                - 'RPC' (custom level): logging RPC messages which are sent by RPC protocols.
                - 'TRACE': logging engine output like console output of blender.
                - 'DEBUG': logging debug messages.
                - 'INFO': logging info messages.
                - ...
        log_path (Path, optional): path to save the log file. Defaults to None.
        replace (bool, optional): replace the log file if exists. Defaults to True.
    """
    try:
        return LoggerWrapper.setup_logging(level, log_path, replace)
    except Exception as e:
        import traceback

        print(repr(e))
        print(traceback.format_exc())
        raise e


#### (rich) progress bar ####
class SpeedColumn(ProgressColumn):
    """Renders the speed of a task."""

    def render(self, task: 'Task') -> Text:
        speed = task.speed
        if speed is None:
            return Text('N/A', style='progress.data.speed')
        return Text(f'{1/speed:.1f} s/step', style='progress.data.speed')


class TimeProgress(Progress):
    @classmethod
    def get_default_columns(cls) -> Tuple[Union[ProgressColumn, str], ...]:
        return (
            TextColumn('{task.description}'),
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn(show_speed=True),
            '• Remaining',
            TimeRemainingColumn(),
            '• Elapsed',
            TimeElapsedColumn(),
            '•',
            SpeedColumn(),
        )


def track(
    sequence: Union[Sequence[ProgressType], Iterable[ProgressType]],
    description: str = 'Working...',
    total: Optional[float] = None,
    disable: bool = False,
) -> Iterable[ProgressType]:
    """Custom Track progress by iterating over a sequence."""
    progress = TimeProgress(
        speed_estimate_period=24 * 60 * 60,
        refresh_per_second=1,
        disable=disable,
    )  # 1 day as speed estimate period for long task
    with progress:
        yield from progress.track(
            sequence,
            total=total,
            description=description,
        )
