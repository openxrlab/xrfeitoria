.. _FAQ:

Frequently Asked Questions
==========================

We list some common troubles faced by many users and their corresponding solutions here.
Feel free to enrich the list if you find any frequent issues and have ways to help others to solve them.
If the contents here do not cover your issue, do not hesitate to create an issue!

-----------

API
----

.. _FAQ-Plugin:

How to use the plugin of Blender/Unreal under development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First you should clone the repo of XRFeitoria, and maybe modify the code of the plugin under ``src/XRFeitoriaBlender`` or ``src/XRFeitoriaUnreal``.
Then you can use the plugin under development by setting ``dev_plugin=True`` in :class:`init_blender <xrfeitoria.factory.init_blender>` or :class:`init_unreal <xrfeitoria.factory.init_unreal>`.

You can install the plugin by:

.. tabs::
    .. tab:: Blender
        .. code-block:: bash
            :linenos:

            git clone https://github.com/openxrlab/xrfeitoria.git
            cd xrfeitoria
            pip install -e .
            python -c "import xrfeitoria as xf; xf.init_blender(replace_plugin=True, dev_plugin=True)"

            # or through the code in tests
            python -m tests.blender.init --dev [-b]

    .. tab:: Unreal
        .. code-block:: bash
            :linenos:

            git clone https://github.com/openxrlab/xrfeitoria.git
            cd xrfeitoria
            pip install -e .
            python -c "import xrfeitoria as xf; xf.init_unreal(replace_plugin=True, dev_plugin=True)"

            # or through the code in tests
            python -m tests.unreal.init --dev [-b]


Build plugins
^^^^^^^^^^^^^^

If you want to publish plugins of your own, you can use the following command:

.. code-block:: powershell
    :linenos:

    # install xrfeitoria first
    cd xrfeitoria
    pip install .

    # for instance, build plugins for Blender, UE 5.1, UE 5.2, and UE 5.3 on Windows.
    # using powershell where backtick(`) is the line continuation character.
    python -m xrfeitoria.utils.publish_plugins `
      -u "C:/Program Files/Epic Games/UE_5.1/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" `
      -u "C:/Program Files/Epic Games/UE_5.2/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" `
      -u "C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"

Please check the path ``./src/dist`` for the generated plugins.
``XRFeitoriaBlender`` will be archived by default, and ``XRFeitoriaUnreal`` will only be built when you specify the Unreal editor path.
Make sure you have installed the corresponding Unreal Engine and Visual Studio before building the unreal plugin.

Find out the plugin version in ``./xrfeitoria/version.py``. Or by:

.. code-block:: bash

    >>> python -c "import xrfeitoria; print(xrfeitoria.__version__)"
    0.6.1.dev10+gd12997e.d20240122

You can set the environment variable ``XRFEITORIA__DIST_ROOT`` and ``XRFEITORIA__VERSION`` to change the plugins used by XRFeitoria.
And run your code ``xxx.py`` like:

.. tabs::
    .. tab:: UNIX

        .. code-block:: bash

            XRFEITORIA__DIST_ROOT=/path/to/src/dist \
            XRFEITORIA__VERSION=0.6.1.dev10+gd12997e.d20240122 \
                python xxx.py

    .. tab:: Windows

        .. code-block:: powershell

            $env:XRFEITORIA__DIST_ROOT="C:/path/to/src/dist"; `
            $env:XRFEITORIA__VERSION="0.6.1.dev10+gd12997e.d20240122"; `
                python xxx.py

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

        .. code-block:: powershell

            $env:BLENDER_PORT=50051; python xxx.py

-----------

Known Issues
-------------

Inaccurate vertices in Unreal Engine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _XRFeitoriaUnreal: https://github.com/openxrlab/xrfeitoria/tree/main/src/XRFeitoriaUnreal

The vertices exported from actors in Unreal Engine may be inaccurate. This is a issue in `XRFeitoriaUnreal`_ plugin.
