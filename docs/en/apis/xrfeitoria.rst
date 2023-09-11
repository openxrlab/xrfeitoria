xrfeitoria
==================

Initialize firstly and run xrfeitoria.


.. tabs::
    .. tab:: Blender

        .. code-block:: python
            :linenos:
            :emphasize-lines: 2

            import xrfeitoria as xf
            with xf.init_blender() as xf_runner:
                ...

        ``xf_runner`` is an instance of :class:`XRFeitoriaBlender <xrfeitoria.factory.XRFeitoriaBlender>`,
        where contains all the classes and methods to run xrfeitoria.


    .. tab:: Unreal

        .. code-block:: python
            :linenos:
            :emphasize-lines: 2

            import xrfeitoria as xf
            with xf.init_unreal() as xf_runner:
                ...

        ``xf_runner`` is an instance of :class:`XRFeitoriaUnreal <xrfeitoria.factory.XRFeitoriaUnreal>`,
        where contains all the classes and methods to run xrfeitoria.

After initialized, use members of ``xf_runner``.

Ref to members of :class:`XRFeitoriaBlender <xrfeitoria.factory.XRFeitoriaBlender>` and
:class:`XRFeitoriaUnreal <xrfeitoria.factory.XRFeitoriaUnreal>`.

.. _Tutorial01: ../src/tutorials/01_get_started.ipynb

.. seealso::
    Ref to `Tutorial01`_.

    Ref to docs of :class:`xrfeitoria.init_blender <xrfeitoria.factory.init_blender>` and
    :class:`xrfeitoria.init_unreal <xrfeitoria.factory.init_unreal>`.
