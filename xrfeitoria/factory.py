from typing import Optional

from . import _tls
from .data_structure.constants import EngineEnum, PathLike, default_level_blender

__all__ = ['init_blender', 'init_unreal']


class XRFeitoriaBlender:
    """Factory class contains all the classes and functions for Blender.

    Members:
        :class:`ObjectUtils <xrfeitoria.object.object_utils.ObjectUtilsBlender>`: Object utilities.\n
        :class:`Camera <xrfeitoria.camera.camera_blender.CameraBlender>`: Camera class.\n
        :class:`Actor <xrfeitoria.actor.actor_blender.ActorBlender>`: Actor class.\n
        :class:`Shape <xrfeitoria.actor.actor_blender.ShapeBlenderWrapper>`: Shape wrapper class.\n
        :class:`Renderer <xrfeitoria.renderer.renderer_blender.RendererBlender>`: Renderer class.\n
        :class:`Sequence <xrfeitoria.sequence.sequence_wrapper.SequenceWrapperBlender>`: Sequence wrapper class.\n
        :class:`utils <xrfeitoria.utils.functions.blender_functions>`: Utilities functions executed in Blender.\n
        :meth:`render <xrfeitoria.renderer.renderer_blender.RendererBlender.render_jobs>`: Render jobs.\n
    """

    def __init__(
        self,
        engine_exec: Optional[PathLike] = None,
        project_path: Optional[PathLike] = None,
        background: bool = False,
        replace_plugin: bool = False,
        dev_plugin: bool = False,
        new_process: bool = False,
    ) -> None:
        """Giving arguments to initialize.

        Args:
            new_process (bool, optional): Whether to start Blender in a new process. Defaults to False.
            exec_path (Optional[PathLike], optional): Path to Blender executable. Defaults to None.
            project_path (Optional[PathLike], optional): Path to Blender project. Defaults to None.
            background (bool, optional): Whether to start Blender in background. Defaults to False.
            replace_plugin (bool, optional): Whether to replace the plugin. Defaults to False.
            dev_plugin (bool, optional): Whether to use the plugin under local directory.
                If False, would use the plugin downloaded from a remote server. Defaults to False.
            cleanup (bool, optional): Whether to clean up the scene. Defaults to True.
        """
        from .object.object_utils import ObjectUtilsBlender  # isort:skip
        from .camera.camera_blender import CameraBlender  # isort:skip
        from .actor.actor_blender import ActorBlender, ShapeBlenderWrapper  # isort:skip
        from .renderer.renderer_blender import RendererBlender  # isort:skip
        from .sequence.sequence_wrapper import SequenceWrapperBlender  # isort:skip
        from .utils.runner import BlenderRPCRunner  # isort:skip
        from .utils.functions import blender_functions  # isort:skip
        from .utils.tools import Logger  # isort:skip

        self.logger = Logger.setup_logging()  # default level is INFO
        self.ObjectUtils = ObjectUtilsBlender
        self.Camera = CameraBlender
        self.Actor = ActorBlender
        self.Shape = ShapeBlenderWrapper
        self.Renderer = RendererBlender
        self.render = self.Renderer.render_jobs
        self.Sequence = SequenceWrapperBlender
        self.utils = blender_functions
        self._rpc_runner = BlenderRPCRunner(
            engine_exec=engine_exec,
            project_path=project_path,
            replace_plugin=replace_plugin,
            dev_plugin=dev_plugin,
            background=background,
            new_process=new_process,
        )


class XRFeitoriaUnreal:
    """Factory class contains all the classes and functions for Unreal.

    Members:
        :class:`ObjectUtils <xrfeitoria.object.object_utils.ObjectUtilsUnreal>`: Object utilities.\n
        :class:`Camera <xrfeitoria.camera.camera_unreal.CameraUnreal>`: Camera class.\n
        :class:`Actor <xrfeitoria.actor.actor_unreal.ActorUnreal>`: Actor class.\n
        :class:`Shape <xrfeitoria.actor.actor_unreal.ShapeUnrealWrapper>`: Shape wrapper class.\n
        :class:`Renderer <xrfeitoria.renderer.renderer_unreal.RendererUnreal>`: Renderer class.\n
        :class:`Sequence <xrfeitoria.sequence.sequence_wrapper.SequenceWrapperUnreal>`: Sequence wrapper class.\n
        :class:`utils <xrfeitoria.utils.functions.unreal_functions>`: Utilities functions executed in Unreal.\n
        :meth:`render <xrfeitoria.renderer.renderer_unreal.RendererUnreal.render_jobs>`: Render jobs.\n
    """

    def __init__(
        self,
        engine_exec: Optional[PathLike] = None,
        project_path: Optional[PathLike] = None,
        background: bool = False,
        replace_plugin: bool = False,
        dev_plugin: bool = False,
        new_process: bool = False,
    ) -> None:
        """Giving arguments to initialize.

        Args:
            exec_path (Optional[PathLike], optional): Path to Unreal executable. Defaults to None.
            project_path (Optional[PathLike], optional): Path to Unreal project. Defaults to None.
            background (bool, optional): Whether to start Unreal in background. Defaults to False.
            replace_plugin (bool, optional): Whether to replace the plugin. Defaults to False.
            dev_plugin (bool, optional): Whether to use the plugin under local directory.
                If False, would use the plugin downloaded from a remote server. Defaults to False.
            new_process (bool, optional): Whether to start Unreal in a new process. Defaults to False.
        """
        from .object.object_utils import ObjectUtilsUnreal  # isort:skip
        from .camera.camera_unreal import CameraUnreal  # isort:skip
        from .actor.actor_unreal import ActorUnreal, ShapeUnrealWrapper  # isort:skip
        from .renderer.renderer_unreal import RendererUnreal  # isort:skip
        from .sequence.sequence_wrapper import SequenceWrapperUnreal  # isort:skip
        from .utils.runner import UnrealRPCRunner  # isort:skip
        from .utils.functions import unreal_functions  # isort:skip
        from .utils.tools import Logger  # isort:skip

        self.logger = Logger.setup_logging()  # default level is INFO
        self.ObjectUtils = ObjectUtilsUnreal
        self.Camera = CameraUnreal
        self.Actor = ActorUnreal
        self.Shape = ShapeUnrealWrapper
        self.Renderer = RendererUnreal
        self.render = self.Renderer.render_jobs
        self.Sequence = SequenceWrapperUnreal
        self.utils = unreal_functions
        self._rpc_runner = UnrealRPCRunner(
            engine_exec=engine_exec,
            project_path=project_path,
            replace_plugin=replace_plugin,
            dev_plugin=dev_plugin,
            background=background,
            new_process=new_process,
        )


class init_blender(XRFeitoriaBlender):
    """Initialize Blender with ``XRFeitoria``, which would start Blender as RPC server,
    and yield a :class:`~xrfeitoria.factory.XRFeitoriaBlender` object.

    Examples:
        - Use as context manager:

            >>> import xrfeitoria as xf
            >>> with xf.init_blender() as xf_runner:
            >>>     ...

        - Or use directly:

            >>> import xrfeitoria as xf
            >>> xf_runner = xf.init_blender()
            >>> ...
            >>> xf_runner.close()

    Yields:
        :class:`~xrfeitoria.factory.XRFeitoriaBlender`: XRFeitoria Factory class for Blender.
    """

    def __init__(
        self,
        new_process: bool = False,
        exec_path: Optional[PathLike] = None,
        project_path: Optional[PathLike] = None,
        background: bool = False,
        replace_plugin: bool = False,
        dev_plugin: bool = False,
        cleanup: bool = True,
    ) -> None:
        """Giving arguments to initialize.

        Args:
            new_process (bool, optional): Whether to start Blender in a new process. Defaults to False.
            exec_path (Optional[PathLike], optional): Path to Blender executable. Defaults to None.
            project_path (Optional[PathLike], optional): Path to Blender project. Defaults to None.
            background (bool, optional): Whether to start Blender in background. Defaults to False.
            replace_plugin (bool, optional): Whether to replace the plugin. Defaults to False.
            dev_plugin (bool, optional): Whether to use the plugin under local directory.
                If False, would use the plugin downloaded from a remote server. Defaults to False.
            cleanup (bool, optional): Whether to clean up the scene. Defaults to True.

        Note:
            If ``dev_plugin=True``, the plugin under local directory would be used,
            which is under ``src/XRFeitoriaBlender``.
            You should git clone first, and then use this option if you want to develop the plugin.

            .. code-block:: bash
                :linenos:

                git clone https://github.com/openxrlab/xrfeitoria.git
                cd xrfeitoria
                pip install -e .
                python -c "import xrfeitoria as xf; xf.init_blender(replace_plugin=True, dev_plugin=True)"
        """
        _tls.cache['platform'] = EngineEnum.blender
        self._cleanup = cleanup
        super().__init__(
            engine_exec=exec_path,
            project_path=project_path,
            replace_plugin=replace_plugin,
            dev_plugin=dev_plugin,
            background=background,
            new_process=new_process,
        )
        self._rpc_runner.start()
        self.utils.init_scene_and_collection(default_level_blender, self._cleanup)

    def __enter__(self) -> 'init_blender':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        self.Renderer.clear()
        self._rpc_runner.stop()


class init_unreal(XRFeitoriaUnreal):
    """Initialize Unreal with ``XRFeitoria``, which would start Unreal as RPC server,
    and yield a :class:`~xrfeitoria.factory.XRFeitoriaUnreal` object.

    Examples:
        - Use as context manager:

            >>> import xrfeitoria as xf
            >>> with xf.init_unreal() as xf_runner:
            >>>     ...

        - Or use directly:

            >>> import xrfeitoria as xf
            >>> xf_runner = xf.init_unreal()
            >>> ...
            >>> xf_runner.close()

    Yields:
        :class:`~xrfeitoria.factory.XRFeitoriaUnreal`: XRFeitoria Factory class for Unreal.
    """

    def __init__(
        self,
        exec_path: Optional[PathLike] = None,
        project_path: Optional[PathLike] = None,
        background: bool = False,
        replace_plugin: bool = False,
        dev_plugin: bool = False,
        new_process: bool = False,
    ) -> None:
        """Giving arguments to initialize.

        Args:
            exec_path (Optional[PathLike], optional): Path to Unreal executable. Defaults to None.
            project_path (Optional[PathLike], optional): Path to Unreal project. Defaults to None.
            background (bool, optional): Whether to start Unreal in background. Defaults to False.
            replace_plugin (bool, optional): Whether to replace the plugin. Defaults to False.
            dev_plugin (bool, optional): Whether to use the plugin under local directory.
                If False, would use the plugin downloaded from a remote server. Defaults to False.
            new_process (bool, optional): Whether to start Unreal in a new process. Defaults to False.

        Note:
            If ``dev_plugin=True``, the plugin under local directory would be used,
            which is under ``src/XRFeitoriaUnreal``.
            You should git clone first, and then use this option if you want to develop the plugin.

            .. code-block:: bash
                :linenos:

                git clone https://github.com/openxrlab/xrfeitoria.git
                cd xrfeitoria
                pip install -e .
                python -c "import xrfeitoria as xf; xf.init_unreal(replace_plugin=True, dev_plugin=True)"
        """
        _tls.cache['platform'] = EngineEnum.unreal
        _tls.cache['unreal_project_path'] = project_path
        super().__init__(
            engine_exec=exec_path,
            project_path=project_path,
            replace_plugin=replace_plugin,
            dev_plugin=dev_plugin,
            background=background,
            new_process=new_process,
        )
        # xf_runner.Renderer.clear()
        self._rpc_runner.start()

    def __enter__(self) -> 'init_unreal':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        """Close the RPC server."""
        self.Renderer.clear()
        self._rpc_runner.stop()
