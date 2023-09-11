"""Utils tools for logging and progress bar."""


from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple, Union

import loguru
from loguru import logger
from rich import print as rprint
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

__all__ = ['Logger']


class Logger:
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
        cls, level: str = 'INFO', log_path: 'Optional[PathLike]' = None, replace: bool = True
    ) -> 'loguru.Logger':
        """Setup logging to file and console.

        Args:
            level (str, optional): logging level. Defaults to "INFO", can be "DEBUG", "INFO", "WARNING",
                                    "ERROR", "CRITICAL".
            log_path (Path, optional): path to save the log file. Defaults to None.
            replace (bool, optional): replace the log file if exists. Defaults to True.
        """
        if cls.is_setup:
            return logger

        logger.remove()  # remove default logger
        logger.add(sink=lambda msg: rprint(msg, end=''), level=level, format=cls.logger_format)
        # logger.add(RichHandler(level=level, rich_tracebacks=True, markup=True), level=level, format='{message}')
        if log_path:
            # add file logger
            log_path = Path(log_path).resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if replace and log_path.exists():
                log_path.unlink(missing_ok=True)
            logger.add(log_path, level='DEBUG', filter=cls.filter_unique, format=cls.logger_format, encoding='utf-8')
            logger.info(f'Python Logging to "{log_path.as_posix()}"')
        cls.is_setup = True
        return logger


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
