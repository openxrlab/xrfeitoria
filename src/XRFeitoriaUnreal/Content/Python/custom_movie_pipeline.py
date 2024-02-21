import os
from typing import Callable, Dict, List, Optional, Tuple

import unreal
import utils
from constants import (
    ENGINE_MAJOR_VERSION,
    ENGINE_MINOR_VERSION,
    MATERIAL_PATHS,
    PROJECT_ROOT,
    RenderJobUnreal,
    RenderPass,
    SubSystem,
    UnrealRenderLayerEnum,
)

# define the post process material to the render_pass
material_paths = MATERIAL_PATHS
material_path_keys = [key.lower() for key in material_paths.keys()]


class CustomMoviePipeline:
    """This class contains several class methods, which are used to control the movie
    pipeline (Movie Render Queue), including:

    - clearQueue: Clear the movie render queue.
    - addJobToQueueWithYAMLConfig: Add a job to the movie render queue with yaml config.
    - renderQueue: Render the jobs in movie render queue.
    - ...
    """

    subsystem = SubSystem.MoviePipelineQueueSub
    pipeline_queue = subsystem.get_queue()

    host = '127.0.0.1'
    socket_port = int(os.environ.get('SOCKET_PORT', 9999))
    jobs: List[str] = []
    executor = None

    @classmethod
    def init_executor(cls):
        if cls.executor is None:
            cls.executor = unreal.MoviePipelinePIEExecutor()
        cls.executor.connect_socket(cls.host, cls.socket_port)
        cls.log_msg_with_socket('Socket of Unreal Renderer Connected')

    @classmethod
    def close_executor(cls):
        if cls.executor is not None:
            cls.executor.disconnect_socket()
            cls.executor = None

    @classmethod
    def clear_queue(cls) -> None:
        for job in cls.pipeline_queue.get_jobs():
            unreal.log('Deleting job ' + job.job_name)
            cls.pipeline_queue.delete_job(job)
        cls.jobs.clear()

        if cls.executor is not None:
            unreal.log('Disconnecting socket')
            cls.executor.disconnect_socket()
            cls.executor = None
        unreal.log('Queue cleared')

    @classmethod
    def save_queue(cls, path: str) -> None:
        """Save the movie render queue."""
        unreal.MoviePipelineEditorLibrary.save_queue_to_manifest_file(cls.pipeline_queue)
        manifest_file = PROJECT_ROOT / 'Saved/MovieRenderPipeline/QueueManifest.utxt'
        manifest_str = unreal.MoviePipelineEditorLibrary.convert_manifest_file_to_string(manifest_file.as_posix())
        with open(path, 'w') as f:
            f.write(manifest_str)
        unreal.log(f"Saved queue to '{path}' as a manifest file.")

    @classmethod
    def get_job_length(cls) -> int:
        return len(cls.pipeline_queue.get_jobs())

    @staticmethod
    def get_output_path(movie_preset: unreal.MoviePipelineMasterConfig) -> str:
        """Get output path from a movie preset.

        Args:
            movie_preset (unreal.MoviePipelineMasterConfig): The movie preset to get output path from.

        Returns:
            str: The output path.
        """
        output_config: unreal.MoviePipelineOutputSetting = movie_preset.find_or_add_setting_by_class(
            unreal.MoviePipelineOutputSetting
        )
        return output_config.output_directory.path

    @staticmethod
    def set_render_all_cameras(movie_preset: unreal.MoviePipelineMasterConfig, enable: bool = True) -> None:
        camera_setting: unreal.MoviePipelineCameraSetting = movie_preset.find_or_add_setting_by_class(
            unreal.MoviePipelineCameraSetting
        )
        camera_setting.render_all_cameras = enable

    @staticmethod
    def set_export_audio(movie_preset: unreal.MoviePipelineMasterConfig) -> None:
        export_setting: unreal.MoviePipelineWaveOutput = movie_preset.find_or_add_setting_by_class(
            unreal.MoviePipelineWaveOutput
        )

    @staticmethod
    def add_render_passes(movie_preset: unreal.MoviePipelineMasterConfig, render_passes: List[RenderPass]) -> None:
        """Add render passes to a movie preset.

        Args:
            movie_preset (unreal.MoviePipelineMasterConfig): The movie preset to add render passes to.
            render_passes (List[RenderPass]): The render passes to add.
                The available render passes are defined in `UnrealRenderLayerEnum`: `rgb`, `depth`, `mask`, \
                `flow`, `diffuse`, `normal`, `metallic`, `roughness`, `specular`, `tangent`, `basecolor`
        """

        # find or add setting
        render_pass = movie_preset.find_or_add_setting_by_class(unreal.CustomMoviePipelineDeferredPass)
        render_pass_config = movie_preset.find_or_add_setting_by_class(unreal.CustomMoviePipelineOutput)

        # add render passes
        additional_render_passes = []
        for render_pass in render_passes:
            pass_name = render_pass.render_layer.value
            enable = True
            ext = getattr(unreal.CustomImageFormat, render_pass.image_format.value.upper())  # convert to unreal enum

            if pass_name.lower() == UnrealRenderLayerEnum.img.value.lower():
                render_pass_config.enable_render_pass_rgb = enable
                render_pass_config.render_pass_name_rgb = pass_name
                render_pass_config.extension_rgb = ext
            elif pass_name.lower() in material_path_keys:
                # material = unreal.SoftObjectPath(material_map[pass_name])
                material = unreal.load_asset(material_paths[pass_name.lower()])
                _pass = unreal.CustomMoviePipelineRenderPass(
                    enabled=enable, material=material, render_pass_name=pass_name, extension=ext
                )
                additional_render_passes.append(_pass)

        render_pass_config.additional_render_passes = additional_render_passes

    @staticmethod
    def add_output_config(
        movie_preset: unreal.MoviePipelineMasterConfig,
        resolution: Tuple[int, int] = [1920, 1080],
        file_name_format: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> None:
        """Add output config to a movie preset.

        Args:
            movie_preset (unreal.MoviePipelineMasterConfig): The movie preset to add output config to.
            resolution (list): Resolution of the output, e.g. [1920, 1080].
            file_name_format (str): Format of the output file name, e.g. '{sequence_name}/{render_pass}/{frame_number}'
            output_path (str): Path of the output, e.g. 'E:/output'
        """
        # find or add setting
        output_config = movie_preset.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)

        # add resolution settings
        output_config.output_resolution = unreal.IntPoint(resolution[0], resolution[1])

        # add file name format settings
        if file_name_format:
            output_config.file_name_format = file_name_format

        # set output path
        if output_path is not None:
            output_config.output_directory = unreal.DirectoryPath(output_path)

    @staticmethod
    def add_console_command(
        movie_preset: unreal.MoviePipelineMasterConfig,
        console_variables: Dict[str, float] = {'r.MotionBlurQuality': 0.0},
    ) -> None:
        """Add console command to a movie preset. Now only support motion blur.

        Args:
            movie_preset (unreal.MoviePipelineMasterConfig): The movie preset to add console command to.
            console_variables (dict): Console variables.
        """
        # find or add setting
        console_config: unreal.MoviePipelineConsoleVariableSetting = movie_preset.find_or_add_setting_by_class(
            unreal.MoviePipelineConsoleVariableSetting
        )
        if ENGINE_MAJOR_VERSION >= 5 and ENGINE_MINOR_VERSION >= 2:
            for key, value in console_variables.items():
                console_config.add_or_update_console_variable(key, value)
        else:
            console_config.console_variables = console_variables

    @staticmethod
    def add_anti_alias(
        movie_preset: unreal.MoviePipelineMasterConfig,
        anti_alias: RenderJobUnreal.AntiAliasSetting = RenderJobUnreal.AntiAliasSetting(),
    ) -> None:
        """Add anti-alias settings to a movie preset.

        Args:
            movie_preset (unreal.MoviePipelineMasterConfig): The movie preset to add anti-alias settings to.
            anti_alias (dict): Anti-alias settings.
        """
        if not anti_alias.enable:
            return

        # add anti_alias settings
        anti_alias_config: unreal.MoviePipelineAntiAliasingSetting = movie_preset.find_or_add_setting_by_class(
            unreal.MoviePipelineAntiAliasingSetting
        )
        anti_alias_config.spatial_sample_count = anti_alias.spatial_samples
        anti_alias_config.temporal_sample_count = anti_alias.temporal_samples
        if anti_alias.override_anti_aliasing:
            anti_alias_config.override_anti_aliasing = True
        if anti_alias.warmup_frames:
            anti_alias_config.use_camera_cut_for_warm_up = True
            anti_alias_config.render_warm_up_count = anti_alias.warmup_frames
        if anti_alias.render_warmup_frame:
            anti_alias_config.render_warm_up_frames = True

    @classmethod
    def add_settings_to_movie_preset(
        cls,
        movie_preset: unreal.MoviePipelineMasterConfig,
        render_passes: List[RenderPass],
        resolution: Tuple[int, int] = [1920, 1080],
        file_name_format: Optional[str] = None,
        output_path: Optional[str] = None,
        anti_alias: RenderJobUnreal.AntiAliasSetting = RenderJobUnreal.AntiAliasSetting(),
        console_variables: dict = {'r.MotionBlurQuality': 0.0},
    ) -> unreal.MoviePipelineMasterConfig:
        """Add settings to a movie preset.

        Args:
            movie_preset (unreal.MoviePipelineMasterConfig): The movie preset to add settings to.
            render_passes (list): definition of render passes.
            resolution (list): Resolution of the output, e.g. [1920, 1080].
            file_name_format (str): Format of the output file name, e.g. '{sequence_name}/{render_pass}/{frame_number}'
            output_path (str): Path of the output, e.g. 'E:/output'
            anti_alias (dict): Anti-alias settings.
            console_variables (dict): Console variables.

        Returns:
            unreal.MoviePipelineMasterConfig: The created movie preset.
        """

        cls.add_render_passes(movie_preset, render_passes)
        cls.add_output_config(movie_preset, resolution, file_name_format, output_path)
        cls.add_anti_alias(movie_preset, anti_alias)
        cls.add_console_command(movie_preset, console_variables)

        unreal.EditorAssetLibrary.save_loaded_asset(movie_preset)
        return movie_preset

    @classmethod
    def create_movie_preset(
        cls,
        render_passes: List[RenderPass],
        resolution: Tuple[int, int] = [1920, 1080],
        file_name_format: Optional[str] = None,
        output_path: Optional[str] = None,
        anti_alias: RenderJobUnreal.AntiAliasSetting = RenderJobUnreal.AntiAliasSetting(),
        console_variables: Dict[str, float] = {'r.MotionBlurQuality': 0.0},
        export_audio: bool = False,
    ) -> unreal.MoviePipelineMasterConfig:
        """
        Create a movie preset from args.
        1. Add render passes which contains the name of the render pass, and the extension of the output.
        2. Set output config which contains the resolution, the file name format, and the output path.
        3. Add anti-alias settings.
        4. Add console command, which contains the console variables like motion blur. (https://docs.unrealengine.com/5.2/en-US/rendering-high-quality-frames-with-movie-render-queue-in-unreal-engine/#step7:configuretheconsolevariables)
        5. Set render all cameras to True, which means multi-view rendering simultaneously.

        Args:
            render_passes (list): definition of render passes.
            resolution (list): Resolution of the output, e.g. [1920, 1080].
            file_name_format (str): Format of the output file name, e.g. '{sequence_name}/{render_pass}/{frame_number}'
            output_path (str): Path of the output, e.g. 'E:/output'
            anti_alias (dict): Anti-alias settings.
            console_variables (bool): Console variables.
            export_audio (bool): Whether to export audio.

        Returns:
            unreal.MoviePipelineMasterConfig: The created movie preset.
        """

        movie_preset = unreal.MoviePipelineMasterConfig()

        cls.add_render_passes(movie_preset, render_passes)
        cls.add_output_config(movie_preset, resolution, file_name_format, output_path)
        cls.add_anti_alias(movie_preset, anti_alias)
        cls.add_console_command(movie_preset, console_variables)
        cls.set_render_all_cameras(movie_preset, enable=True)
        if export_audio:
            cls.set_export_audio(movie_preset)

        return movie_preset

    @classmethod
    def create_job(
        cls,
        level: str,
        level_sequence: str,
    ) -> unreal.MoviePipelineExecutorJob:
        # check if assets exist
        if not (
            unreal.EditorAssetLibrary.does_asset_exist(level)
            and unreal.EditorAssetLibrary.does_asset_exist(level_sequence)
        ):
            return False

        # Create a new job and add it to the queue.
        new_job = cls.pipeline_queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
        # TODO: if failed, new_job = False. Need to handle this case.
        new_job.job_name = str(level_sequence.rsplit('/', 1)[-1])
        new_job.map = utils.get_soft_object_path(level)
        new_job.sequence = utils.get_soft_object_path(level_sequence)

        return new_job

    @classmethod
    def add_job_to_queue_with_preset(
        cls,
        level: str,
        level_sequence: str,
        config: str,
    ) -> bool:
        """Add a job to the queue with a pre-defined preset.

        Args:
            level (str): level path in unreal engine.
            level_sequence (str): level sequence path in unreal engine.
            config (str): pre-defined preset path in unreal engine.

        Returns:
            bool: success or not.
        """
        new_job = cls.create_job(level, level_sequence)
        if not new_job:
            return False
        movie_preset = unreal.load_asset(config)
        new_job.set_configuration(movie_preset)
        unreal.log(f'Added new job ({new_job.job_name}) to queue')
        return True

    @classmethod
    def log_msg_with_socket(
        cls,
        msg: str,
        executor: Optional[unreal.MoviePipelinePIEExecutor] = None,
    ):
        """Log message with socket."""
        if executor is None:
            if cls.executor is None:
                cls.init_executor()
            executor = cls.executor
        executor.send_socket_message(msg)
        unreal.log(msg)

    @classmethod
    def add_job_to_queue(cls, job: RenderJobUnreal) -> bool:
        """Add a job to the queue.

        Args:
            job (RenderJobUnreal): a render job.

        Returns:
            bool: success or not.
        """
        new_job = cls.create_job(job.map_path, job.sequence_path)
        if not new_job:
            return False
        movie_preset = cls.create_movie_preset(
            render_passes=job.render_passes,
            resolution=job.resolution,
            file_name_format=job.file_name_format,
            output_path=job.output_path,
            anti_alias=job.anti_aliasing,
            console_variables=job.console_variables,
            export_audio=job.export_audio,
        )
        new_job.set_configuration(movie_preset)
        unreal.log(f'Added new job ({new_job.job_name}) to queue')
        return True

    @classmethod
    def add_job_to_queue_with_render_config(
        cls,
        level: str,
        level_sequence: str,
        render_config: Optional[dict] = None,
    ) -> bool:
        """Add a job to the queue with a YAML config loaded from a file.

        Args:
            level (str): level path in unreal engine.
            level_sequence (str): level sequence path in unreal engine.
            render_config (dict): YAML config loaded from a file. You can
                find a template in `data/render_config.yaml`.

        Returns:
            bool: success or not.

        Examples:
            >>> render_config = {
                    'Resolution': [1920, 1080],
                    'Output_Path': 'E:/Datasets/tmp',
                    'File_Name_Format': '{sequence_name}/{render_pass}/{frame_number}',
                    'Console_Variables': {'r.MotionBlurQuality': 0.0},
                    'Anti_Alias': {'enable': False, 'spatial_samples': 8, 'temporal_samples': 8},
                    'Render_Passes': [
                        {'pass_name': 'img', 'enable': True, 'ext': 'jpeg'},
                        {'pass_name': 'depth', 'enable': True, 'ext': 'exr'},
                        {'pass_name': 'mask', 'enable': True, 'ext': 'exr'},
                        {'pass_name': 'flow', 'enable': True, 'ext': 'exr'},
                        {'pass_name': 'normal', 'enable': True, 'ext': 'png'}
                    ]
                }
            >>> # or you can use the following code to load the config from a file
            >>> from data.config import CfgNode
            >>> render_config = CfgNode.load_yaml_with_base(PLUGIN_ROOT / 'misc/render_config_common.yaml')
            >>> #
            >>> CustomMoviePipeline.add_job_to_queue_with_render_config(
                    level='/Game/ThirdPerson/Maps/ThirdPersonMap',
                    level_sequence='/Game/NewLevelSequence',
                    render_config=render_config
                )
        """
        newJob = cls.create_job(level, level_sequence)
        if not newJob:
            return False
        if render_config is None:
            render_config = cls.render_config
        movie_preset = cls.create_movie_preset(
            render_passes=render_config['Render_Passes'],
            resolution=render_config['Resolution'],
            file_name_format=render_config['File_Name_Format'],
            output_path=render_config['Output_Path'],
            anti_alias=render_config['Anti_Alias'],
            console_variables=render_config['Console_Variables'],
        )
        newJob.set_configuration(movie_preset)
        unreal.log(f'Added new job ({newJob.job_name}) to queue')
        return True

    def onQueueFinishedCallback(executor: unreal.MoviePipelineLinearExecutorBase, success: bool):
        """On queue finished callback. This is called when the queue finishes. The args
        are the executor and the success of the queue, and it cannot be modified.

        Args:
            executor (unreal.MoviePipelineLinearExecutorBase): The executor of the queue.
            success (bool): Whether the queue finished successfully.
        """
        # TODO: bug fix
        mss = f'     Render completed. Success: {success}'
        CustomMoviePipeline.log_msg_with_socket(mss, executor)

    def onIndividualJobFinishedCallback(inJob: unreal.MoviePipelineExecutorJob, success: bool):
        """On individual job finished callback. This is called when an individual job
        finishes. The args are the job and the success of the job, and it cannot be
        modified.

        Args:
            inJob (unreal.MoviePipelineExecutorJob): The job that finished.
            success (bool): Whether the job finished successfully.
        """

        # get class variable `Jobs` to get the index of the finished job
        jobs = CustomMoviePipeline.jobs

        job_name = inJob.job_name
        job_index = jobs.index(job_name) + 1
        output_path = CustomMoviePipeline.get_output_path(inJob.get_configuration())

        # XXX: for no reason (only in here), the first 4 characters of mss cannot be sent
        mss = f'    job rendered ({job_index}/{len(jobs)}): seq_name="{job_name}", saved to "{output_path}/{job_name}"'
        CustomMoviePipeline.log_msg_with_socket(mss, CustomMoviePipeline.executor)

    @classmethod
    def render_queue(
        cls,
        queue_finished_callback: Callable = onQueueFinishedCallback,
        individual_job_finished_callback: Callable = onIndividualJobFinishedCallback,
    ) -> None:
        """Render the queue. This will render the queue. You can pass a callback
        function to be called when a job or the queue finishes. You can also pass a
        custom executor to use, or the default one will be used.

        Args:
            queue_finished_callback (Callable): The callback function to be called when the queue finishes.
            individual_job_finished_callback (Callable): The callback function to be called when an individual job finishes.
            executor (unreal.MoviePipelineLinearExecutorBase): The custom executor to use, or the default one will be used.
        """
        # check if there's jobs added to the queue
        if len(cls.pipeline_queue.get_jobs()) == 0:
            unreal.log_error('Open the Window > Movie Render Queue and add at least one job to use this example')
            return

        # add job_name to class variable `Jobs` for monitoring progress in the individual job finished callback
        cls.jobs.clear()
        for job in cls.pipeline_queue.get_jobs():
            cls.jobs.append(job.job_name)

        # set callbacks
        if cls.executor is None:
            cls.init_executor()

        cls.executor.on_executor_finished_delegate.add_callable_unique(queue_finished_callback)
        cls.executor.on_individual_job_finished_delegate.add_callable_unique(individual_job_finished_callback)

        # render the queue
        cls.executor.execute(cls.pipeline_queue)
        cls.log_msg_with_socket('Start Render')


def main():
    CustomMoviePipeline.clear_queue()
    CustomMoviePipeline.add_job_to_queue(
        RenderJobUnreal(
            map_path='/Game/Maps/DefaultMap',
            sequence_path='/Game/Sequences/NewSequence',
            resolution=[1920, 1080],
            output_path='E:/Datasets/tmp',
            file_name_format='{sequence_name}/{render_pass}/{frame_number}',
            console_variables={'r.MotionBlurQuality': 0.0},
            anti_alias={'enable': False},
        )
    )
    CustomMoviePipeline.render_queue()


if __name__ == '__main__':
    # from utils import loadRegistry
    # registry = loadRegistry(RenderQueue)
    # registry.register()

    main()
