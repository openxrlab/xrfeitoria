import os
from abc import ABC, abstractmethod
from functools import wraps
from typing import List

from loguru import logger
from rich import get_console

# Get environment variable for spinner disable, defaulting to False if not set
DISABLE_SPINNER = os.environ.get('XRFEITORIA__DISABLE_SPINNER', '').lower() in ('true', '1', 'yes')


# decorator
def render_status(func):
    """Decorator for monitoring rendering status."""
    console = get_console()

    @wraps(func)
    def wrapper(*args, **kwargs):
        if DISABLE_SPINNER:
            ret = func(*args, **kwargs)
            logger.info('[bold green]:white_check_mark: Rendering done![/bold green]')
            return ret
        else:
            with console.status('[bold green]:rocket: Rendering...[/bold green]'):
                ret = func(*args, **kwargs)
            logger.info('[bold green]:white_check_mark: Rendering done![/bold green]')
            return ret

    return wrapper


class RendererBase(ABC):
    """Base renderer class."""

    render_queue: List = []

    @classmethod
    @abstractmethod
    def add_job(cls):
        """Add a rendering job to the renderer queue.

        This method should be implemented in subclasses, e.g.,
        :meth:`RenderBlender <xrfeitoria.renderer.renderer_blender.RendererBlender.add_job>` and
        :meth:`RenderUnreal <xrfeitoria.renderer.renderer_unreal.RendererUnreal.add_job>`.
        """
        pass

    @classmethod
    @abstractmethod
    @render_status
    def render_jobs(cls):
        """Render all jobs in the renderer queue.

        This method should be implemented in subclasses, e.g.,
        :meth:`RenderBlender <xrfeitoria.renderer.renderer_blender.RendererBlender.render_jobs>` and
        :meth:`RenderUnreal <xrfeitoria.renderer.renderer_unreal.RendererUnreal.render_jobs>`.
        """
        pass

    @classmethod
    def clear(cls):
        """Clear all rendering jobs in the renderer queue."""
        logger.warning('[red]Clearing Renderer jobs[/red]')
        cls._clear_queue_in_engine()
        cls.render_queue.clear()

    @staticmethod
    @abstractmethod
    def _clear_queue_in_engine():
        pass
