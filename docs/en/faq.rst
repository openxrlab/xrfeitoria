.. _FAQ:

Frequently Asked Questions
==========================

We list some common troubles faced by many users and their corresponding solutions here.
Feel free to enrich the list if you find any frequent issues and have ways to help others to solve them.
If the contents here do not cover your issue, do not hesitate to create an issue!

API
----

.. _FAQ-stencil-value:

What is ``stencil_value``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``stencil_value`` is to distinguish different actors in the sequence when rendering segmentation masks.
The RGB mask color of actors will be saved in the ``{output_path}/actor_infos.json`` of the render job.

In:
    - :meth:`ActorBase.import_from_file <xrfeitoria.actor.actor_base.ActorBase.import_from_file>`
    - :meth:`SequenceUnreal.spawn_actor <xrfeitoria.sequence.sequence_unreal.SequenceUnreal.spawn_actor>`
    - ...


.. _FAQ-console-variables:

What is ``console_variables``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _Unreal-MRQ-Doc: https://docs.unrealengine.com/5.2/en-US/rendering-high-quality-frames-with-movie-render-queue-in-unreal-engine/#step7:configuretheconsolevariables

``console_variables`` is a dictionary of console variables for configure detailed rendering settings.
Please refer to the official documentation for more details: `Unreal-MRQ-Doc`_.

example:

>>> console_variables = {'r.MotionBlurQuality': 0}  # disable motion blur

In:
    - :attr:`RenderJobUnreal.console_variables <xrfeitoria.data_structure.models.RenderJobUnreal.console_variables>`
    - ...


RPC Port
^^^^^^^^^^^^^^^^^^^^^

The RPC port is used for communication between python and engine (blender/unreal).
If the default port is occupied, or you want to use multiple engines at the same time,
you can set the environment variable ``BLENDER_PORT`` or ``UNREAL_PORT`` to change it.

.. tabs::
    .. tab:: UNIX

        .. code-block:: bash

            BLENDER_PORT=50051 python xxx.py

    .. tab:: Windows

        .. code-block:: bash

            $env:BLENDER_PORT=50051; python xxx.py


Known Issues
-------------

Inaccurate vertices in Unreal Engine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _XRFeitoriaUnreal: https://github.com/openxrlab/xrfeitoria/tree/main/src/XRFeitoriaUnreal

The vertices exported from actors in Unreal Engine may be inaccurate. This is a issue in `XRFeitoriaUnreal`_ plugin.
