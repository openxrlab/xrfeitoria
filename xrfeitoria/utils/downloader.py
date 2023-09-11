"""
From:
https://github.com/Textualize/rich/blob/master/examples/downloader.py

A rudimentary URL downloader (like wget or curl) to demonstrate Rich progress bars.
"""

from functools import partial
from pathlib import Path
from urllib.request import urlopen

from loguru import logger
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn


def download(url: str, dst_dir: Path, verbose: bool = True) -> Path:
    """Download file to the given directory.

    Args:
        url (str): The URL to download.
        dst_dir (Path): The directory to save the file to.
        verbose (bool, optional): Whether to print progress. Defaults to True.

    Returns:
        Path: The path to the downloaded file.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split('/')[-1]
    dst_path = Path(dst_dir).resolve() / filename
    if dst_path.exists():
        logger.debug(f'{dst_path.as_posix()} already exists.')
        return dst_path

    try:
        progress = Progress(
            TextColumn('[bold blue]{task.fields[filename]}', justify='right'),
            BarColumn(bar_width=None),
            '[progress.percentage]{task.percentage:>3.1f}%',
            '•',
            DownloadColumn(),
            '•',
            TransferSpeedColumn(),
            '•',
            TimeRemainingColumn(),
            disable=not verbose,
        )
        with progress:
            task_id = progress.add_task('download', filename=filename, start=False)
            logger.info(f'Requesting {url}')
            response = urlopen(url)
            # This will break if the response doesn't contain content length
            progress.update(task_id, total=int(response.info()['Content-length']))
            with open(dst_path, 'wb') as dst_file:
                progress.start_task(task_id)
                logger.info(f'Downloading to "{dst_path.as_posix()}"')
                for data in iter(partial(response.read, 32768), b''):
                    dst_file.write(data)
                    progress.update(task_id, advance=len(data))
            logger.info(f'Downloaded "{dst_path.as_posix()}"')

    except KeyboardInterrupt:
        logger.info('[red]Cancelling download...')
        logger.info('[red]Deleting incomplete download...')
        dst_path.unlink(missing_ok=True)
        exit(1)

    return dst_path


if __name__ == '__main__':
    # Try with https://releases.ubuntu.com/20.04/ubuntu-20.04.6-desktop-amd64.iso
    import sys

    if sys.argv[1:]:
        download(sys.argv[-1], './')
    else:
        print('Usage:\n\tpython downloader.py URL1 URL2 URL3 (etc)')
