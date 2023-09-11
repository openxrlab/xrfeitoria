import json
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from loguru import logger

from .. import _tls
from ..actor.actor_blender import ActorBlender
from ..camera.camera_blender import CameraBlender
from ..data_structure.constants import (
    ImageFileFormatEnum,
    PathLike,
    RenderEngineEnumBlender,
    RenderOutputEnumBlender,
    actor_info_type,
    tmp_dir,
)
from ..rpc import remote_blender
from ..utils.functions import blender_functions
from .renderer_base import RendererBase, render_status

try:
    from ..data_structure.models import RenderJobBlender, RenderPass  # isort:skip
except ModuleNotFoundError:
    pass

try:
    # only for linting, not imported in runtime
    from XRFeitoriaBpy.core.factory import XRFeitoriaBlenderFactory  # defined in src/XRFeitoriaBpy/core/factory.py
except ModuleNotFoundError:
    pass


def receive_stdout(
    process: subprocess.Popen, in_background: bool, frame_range: Tuple[int, int], job_idx: Optional[int] = None
) -> None:
    """Receive output from the subprocess, and update the spinner.

    Args:
        process (subprocess.Popen): Subprocess of the blender process.
        frame_range (Tuple[int, int]): Frame range of the rendering job.
        job_range (Tuple[int, int]): Job range of all jobs in render queue.
    """
    from rich import get_console
    from rich.spinner import Spinner

    frame_count = 0
    frame_current = frame_range[0] - 1
    frame_length = frame_range[1] - frame_range[0] + 1
    job_info = f' {job_idx}' if job_idx else ''

    console = get_console()
    # TODO: change to progress bar
    try:
        spinner: Spinner = console._live.renderable
    except AttributeError:
        status = console.status('[bold green]:rocket: Rendering...[/bold green]')
        status.start()
        spinner: Spinner = status.renderable

    # init
    __frame_current__ = frame_current
    first_trigger = second_trigger = False
    # start receiving
    while True:
        try:
            data = process.stdout.readline().decode()
        except AttributeError:
            break

        if not data:
            break

        if in_background:
            # Fra:{idx}
            matched_frame_info = re.match(r'.*Fra:(\d+).*', data)
            if matched_frame_info:
                first_trigger = True
                __frame_current__ = int(matched_frame_info.group(1))
            if frame_current != __frame_current__:
                second_trigger = True
            if first_trigger and second_trigger:
                frame_current = __frame_current__
                frame_count += 1
                # XXX: can't leave process early,
                # must have on process reading stdout,
                # otherwise the process will hang
                if frame_count > frame_length:
                    break
                text = f'[bold green]:rocket: Rendering Job{job_info}: frame {frame_count}/{frame_length}[/bold green]'
                spinner.update(text=text)
                # reset
                first_trigger = second_trigger = False
        else:
            # Saved: ...
            matched_save_info = re.match(re.compile(r'.*Saved: .*', flags=re.DOTALL), data)
            #   Time: ...
            matched_time_info = re.match(re.compile(r'.*Time: .*', flags=re.DOTALL), data)
            matched_all_info = re.match(re.compile(r'.*Saved: .*Time: .*', flags=re.DOTALL), data)
            if matched_save_info:
                first_trigger = True
            if matched_time_info:
                second_trigger = True
            if matched_all_info:
                first_trigger = second_trigger = True

            if first_trigger and second_trigger:
                frame_count += 1
                if frame_count > frame_length:
                    break
                text = f'[bold green]:rocket: Rendering Job{job_info}: frame {frame_count}/{frame_length}[/bold green]'
                spinner.update(text=text)
                # reset
                first_trigger = second_trigger = False


@remote_blender(dec_class=True, suffix='_in_engine')
class RendererBlender(RendererBase):
    """Renderer class for Blender."""

    render_queue: 'List[RenderJobBlender]' = []

    @classmethod
    def add_job(
        cls,
        sequence_name: str,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: 'List[RenderPass]',
        render_engine: Union[RenderEngineEnumBlender, Literal['cycles', 'eevee', 'workbench']] = 'cycles',
        render_samples: int = 128,
        transparent_background: bool = False,
        arrange_file_structure: bool = True,
    ) -> None:
        """Add a rendering job with specific settings.

        Args:
            output_path (PathLike): Output path of the rendered images.
            resolution (Tuple[int, int]): Resolution of the rendered images.
            render_passes (List[RenderPass]): Render passes.
            scene_name (str, optional): Name of the scene be rendered. Defaults to 'XRFeitoria'.
            render_engine (Union[RenderEngineEnumBlender, Literal['cycles', 'eevee', 'workbench']], optional): Render engine.
                Defaults to cycles.
            render_samples (int, optional): Render samples. Defaults to 128.
            transparent_background (bool, optional): Transparent background. Defaults to False.
            arrange_file_structure (bool, optional): Arrange output images to every camera's folder. Defaults to True.
        """
        if not isinstance(render_passes, list) or len(render_passes) == 0:
            raise ValueError('render_passes must be a list of RenderPass')

        if not isinstance(render_engine, RenderEngineEnumBlender):
            render_engine = RenderEngineEnumBlender.get(render_engine.lower())
        job = RenderJobBlender(
            sequence_name=sequence_name,
            output_path=Path(output_path).resolve(),
            resolution=resolution,
            render_passes=render_passes,
            render_engine=render_engine,
            render_samples=render_samples,
            transparent_background=transparent_background,
            arrange_file_structure=arrange_file_structure,
        )
        cls.render_queue.append(job)

    @classmethod
    @render_status
    def render_jobs(cls, use_gpu: bool = True) -> None:
        """Render a rendering job.

        Args:
            use_gpu (bool, optional): Use GPU to render. Defaults to True.
        """
        if len(cls.render_queue) == 0:
            logger.warning(
                '[bold red]Skip rendering[/bold red], no render job in the queue. \n'
                ':bulb: Please add a job first via: \n'
                '>>> with xf_runner.Sequence.open(sequence_name=...) as seq:\n'
                '...     seq.add_to_renderer(...)'
            )
            return

        process: subprocess.Popen = _tls.cache.get('engine_process')
        in_background = blender_functions.is_background_mode()
        if use_gpu:
            blender_functions.enable_gpu()

        # render
        for job_idx, job in enumerate(cls.render_queue):
            if len(job.render_passes) == 0:
                raise RuntimeError('No render pass in the render job')

            logger.info(
                f'Job rendering {job_idx + 1}/{len(cls.render_queue)}: '
                f'seq_name="{job.sequence_name}", saving to "{job.output_path.as_posix()}"'
            )
            job.output_path.mkdir(exist_ok=True, parents=True)
            # set tmp path
            tmp_render_path = (tmp_dir / 'blender_render_tmp').as_posix() + '/'
            # set renderer
            active_cameras = cls._set_renderer_in_engine(
                job=job.model_dump(mode='json'),
                tmp_render_path=tmp_render_path,
            )
            # export actor infos
            actor_infos: List[actor_info_type] = []
            for actor_name in blender_functions.get_all_object_in_current_level(obj_type='MESH'):
                actor = ActorBlender(actor_name)
                mask_color = actor.mask_color
                actor_infos.append({'actor_name': actor_name, 'mask_color': mask_color})
            with (job.output_path / RenderOutputEnumBlender.actor_infos.value).open('w') as f:
                json.dump(actor_infos, f, indent=4)

            # start a thread to receive stdout
            output_thread = threading.Thread(
                target=receive_stdout,
                kwargs={
                    'process': process,
                    'in_background': in_background,
                    'frame_range': blender_functions.get_frame_range(),
                    'job_idx': job_idx + 1,
                },
            )
            output_thread.start()

            # render
            cls._render_in_engine()
            # delete tmp path folder
            shutil.rmtree(tmp_render_path)

            # ------ post-processing ------ #

            # export camera parameters
            for camera_name in active_cameras:
                camera = CameraBlender(name=camera_name)
                camera.dump_params(
                    output_path=job.output_path / RenderOutputEnumBlender.camera_params.value / f'{camera_name}.json'
                )

            # arrange output
            if job.arrange_file_structure:
                logger.debug(f'Arranging outputs for {job.output_path}')
                cls._arrange_output(job.render_passes, job.output_path, active_cameras)

    @classmethod
    def _arrange_output(cls, render_passes: 'List[RenderPass]', output_path: PathLike, camera_names: List[str]) -> None:
        """Arrange output images to every camera's folder.

        Args:
            render_passes (List[RenderPass): Render passes of the render job.
            output_path (PathLike): Output path of the render job.
            camera_names (List[str]): all active camera names in the rendered scene.
        """
        import glob

        output_path = Path(output_path)

        for render_pass in render_passes:
            pass_name = RenderOutputEnumBlender.get(render_pass.render_layer).name
            pass_ext = ImageFileFormatEnum.get(render_pass.image_format).name

            if len(camera_names) == 0:
                idx = f'{0:04d}'
                camera_names = [f.name.replace(idx, '') for f in output_path.glob(f'{idx}*.{pass_ext}')]

            pass_dir = output_path / pass_name
            for camera_name in camera_names:
                camera_pass_dir = pass_dir / camera_name
                camera_pass_dir.mkdir(exist_ok=True, parents=True)
                camera_name_escape = glob.escape(camera_name)
                camera_pass_files = pass_dir.glob(f'*{camera_name_escape}.*')
                for camera_pass_file in camera_pass_files:
                    new_camera_pass_file = camera_pass_dir / camera_pass_file.name.replace(camera_name, '')
                    if new_camera_pass_file.exists():
                        new_camera_pass_file.unlink()
                    camera_pass_file.rename(new_camera_pass_file)

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _set_renderer_in_engine(job: 'Dict[str, Any]', tmp_render_path: str) -> None:
        """Set renderer in Blender.

        Args:
            job (Dict[str, Any]): Rendering job.

        Raises:
            RuntimeError: If no active camera in the scene.
        """
        scene = XRFeitoriaBlenderFactory.open_sequence(seq_name=job['sequence_name'])

        # clear compositing nodes
        if scene.node_tree:
            scene.node_tree.nodes.clear()

        # get active cameras in the scene
        active_cameras = XRFeitoriaBlenderFactory.get_active_cameras(scene=scene)
        if len(active_cameras) == 0:
            raise RuntimeError(f'Cannot render, no active camera in "{scene.name}"')

        # set renderer
        XRFeitoriaBlenderFactory.set_render_engine(engine=job['render_engine'], scene=scene)
        XRFeitoriaBlenderFactory.add_render_passes(
            output_path=job['output_path'],
            render_passes=job['render_passes'],
            scene=scene,
        )
        XRFeitoriaBlenderFactory.set_background_transparent(transparent=job['transparent_background'], scene=scene)
        XRFeitoriaBlenderFactory.set_render_samples(render_samples=job['render_samples'], scene=scene)
        XRFeitoriaBlenderFactory.set_resolution(resolution=job['resolution'], scene=scene)

        # set tmp path
        scene.render.filepath = tmp_render_path

        return active_cameras

    @staticmethod
    def _render_in_engine() -> 'List[str]':
        """Render a rendering job.

        Args:
            render_job (Dict[str, Any]): Rendering job.
        """
        # render
        XRFeitoriaBlenderFactory.render()
        # close sequence
        XRFeitoriaBlenderFactory.close_sequence()

    @staticmethod
    def _clear_queue_in_engine():
        # nothing to do
        pass
