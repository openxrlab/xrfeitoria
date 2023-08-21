from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger

from ..camera import CameraUtils
from ..constants import (
    ImageFileFormatEnum,
    PathLike,
    RenderEngineEnumBlender,
    RenderJobBlender,
    RenderLayerEnumBlender,
    RenderPass,
    default_level_blender,
)
from ..rpc import remote_class_blender
from . import RendererBase

try:
    import bpy
except ModuleNotFoundError:
    pass


@remote_class_blender
class RendererBlender(RendererBase):
    render_queue: List[RenderJobBlender] = []

    @classmethod
    def add_job(
        cls,
        output_path: PathLike,
        resolution: Tuple[int, int],
        render_passes: List[RenderPass],
        seq_name: str = default_level_blender,
        render_engine: Union[RenderEngineEnumBlender, str] = RenderEngineEnumBlender.cycles,
        render_samples: int = 128,
        transparent_background: bool = False,
        arrange_file_structure: bool = True,
    ) -> None:
        job = RenderJobBlender(
            sequence_name=seq_name,
            output_path=output_path,
            resolution=resolution,
            render_passes=render_passes,
            render_engine=render_engine,
            render_samples=render_samples,
            transparent_background=transparent_background,
            arrange_file_structure=arrange_file_structure,
        )
        job.render_engine = job.render_engine.value
        cls.render_queue.append(job)

    @classmethod
    def render_jobs(cls, use_gpu: bool = True, arrange_file_structure: bool = True) -> None:
        for job in cls.render_queue:
            camera_names = cls._set_renderer_in_engine(job.model_dump(), use_gpu)
            # TODO: log progress
            cls._render_in_engine(job.model_dump())
            if arrange_file_structure:
                cls.arrange_output(job.render_passes, job.output_path, camera_names)

    @classmethod
    def arrange_output(cls, render_passes: List[RenderPass], output_path: PathLike, camera_names: List[str]) -> int:
        # move the files to the correct folder
        output_path = Path(output_path)

        for render_pass in render_passes:
            pass_name = RenderLayerEnumBlender.get(render_pass.render_layer).name
            pass_ext = ImageFileFormatEnum.get(render_pass.image_format).name

            if len(camera_names) == 0:
                idx = f"{0:04d}"
                camera_names = [f.name.replace(idx, "") for f in output_path.glob(f"{idx}*.{pass_ext}")]

            pass_dir = output_path / pass_name
            for camera_name in camera_names:
                camera_pass_dir = pass_dir / camera_name
                camera_pass_dir.mkdir(exist_ok=True)
                camera_pass_files = pass_dir.glob(f"*{camera_name}.*")
                for camera_pass_file in camera_pass_files:
                    new_camera_pass_file = camera_pass_dir / camera_pass_file.name.replace(camera_name, "")
                    if new_camera_pass_file.exists():
                        new_camera_pass_file.unlink()
                    camera_pass_file.rename(new_camera_pass_file)

    #####################################
    ###### RPC METHODS (Private) ########
    #####################################

    @staticmethod
    def _set_renderer_in_engine(job: "Dict[str, Any]", use_gpu: bool = True) -> None: 
        scene = (
            bpy.data.scenes[job["sequence_name"]] if job["sequence_name"] else bpy.data.scenes[default_level_blender]
        )
        RendererBlenderUtils.set_render_engine(engine=job["render_engine"], scene=scene)
        if use_gpu:
            RendererBlenderUtils.use_gpu_in_engine(scene=scene)
        RendererBlenderUtils.add_render_passes(
            output_path=job["output_path"],
            render_passes=job["render_passes"],
            scene=scene,
        )
        RendererBlenderUtils.set_background_transparent(transparent=job["transparent_background"], scene=scene)
        RendererBlenderUtils.set_render_samples(render_samples=job["render_samples"], scene=scene)
        RendererBlenderUtils.set_resolution(resolution=job["resolution"], scene=scene)

        active_cameras = CameraUtils.get_active_cameras(scene=scene)
        if len(active_cameras) == 0:
            raise RuntimeError("Cannot render, no active camera.")
        return active_cameras

    @staticmethod
    def _render_in_engine(job: "Dict[str, Any]") -> None:
        scene = job["sequence_name"] if job["sequence_name"] else bpy.data.scenes[default_level_blender]
        RendererBlenderUtils.render(scene=scene)


class RendererBlenderUtils:
    @staticmethod
    def render(scene: "bpy.types.Scene") -> None:
        """Render the scene with default settings"""
        bpy.ops.render.render(write_still=True, animation=True, scene=scene)

    @staticmethod
    def add_render_passes(output_path: str, render_passes: "List[Dict[str, str]]", scene: "bpy.types.Scene") -> None:
        bpy.context.window.scene = scene
        for render_pass in render_passes:
            bpy.ops.wm.add_render_pass(
                output_path=output_path,
                render_layer=render_pass["render_layer"],
                format=render_pass["image_format"],
            )

    @staticmethod
    def set_background_transparent(scene: "bpy.types.Scene", transparent: bool = False) -> None:
        """Set the background of the scene to transparent"""
        if transparent:
            scene.render.dither_intensity = 0.0
        scene.render.film_transparent = transparent

    @staticmethod
    def use_gpu_in_engine(scene: "bpy.types.Scene") -> None:
        """Set the background of the scene to transparent"""
        if scene.render.engine == "CYCLES":
            bpy.context.preferences.addons['cycles'].preferences.compute_device_type = "CUDA"
            scene.cycles.device = "GPU"

    @staticmethod
    def set_resolution(resolution: tuple[int, int], scene: "bpy.types.Scene") -> None:
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]
        scene.render.resolution_percentage = 100

    @staticmethod
    def set_render_engine(engine: str, scene: "bpy.types.Scene") -> None:
        """Set the engine of the scene"""
        assert engine in ["CYCLES", "BLENDER_EEVEE"], "Invalid engine, must be `CYCLES` or `BLENDER_EEVEE`"
        scene.render.engine = engine

    @staticmethod
    def set_render_samples(render_samples: int, scene: "bpy.types.Scene") -> None:
        """Set the render samples of the engine"""
        if scene.render.engine == "CYCLES":
            scene.cycles.samples = render_samples
            # self.scene.cycles.time_limit = 20
        elif scene.render.engine == "BLENDER_EEVEE":
            scene.eevee.taa_render_samples = render_samples
