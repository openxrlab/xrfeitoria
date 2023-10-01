.. |check_| raw:: html

    <input checked=""  disabled="" type="checkbox">

.. |uncheck_| raw:: html

    <input disabled="" type="checkbox">

.. _Unreal Engine: https://www.unrealengine.com/en-US/

.. _Blender: https://www.blender.org/

.. _OpenXRLab: https://openxrlab.org.cn/

Welcome to XRFeitoria's documentation!
=============================================

XRFeitoria is a rendering toolbox for generating synthetic data photorealistic with ground-truth annotations.
It is a part of the `OpenXRLab`_ project.

.. raw:: html

    <iframe width="640" height="360" src="https://github.com/openxrlab/xrfeitoria/assets/35397764/1e83bcd4-ae00-4c20-8188-3fe73f7c9c01" frameborder="0" allowfullscreen></iframe>

--------

Major Features
----------------

- Support rendering photorealistic images with ground-truth annotations.
- Support multiple engine backends, including `Unreal Engine`_ and `Blender`_.
- Support assets/camera management, including import, export, and delete.
- Support a CLI tool to render images from a mesh file.

--------

Installation
------------

.. code-block:: bash

    pip install xrfeitoria

    # to use visualization tools
    pip install xrfeitoria[vis]

Requirements
^^^^^^^^^^^^

- ``Python >= 3.8``
- (optional) ``Unreal Engine >= 5.1``
    |check_| Windows
- (optional) `Blender >= 3.0`
    |check_| Windows

    |check_| Linux

    |check_| MacOS

----

.. toctree::
    :maxdepth: 1
    :caption: Beginner's Guide

    src/cli.md
    src/Tutorials.rst
    Samples <https://github.com/openxrlab/xrfeitoria/tree/main/samples>

--------

.. toctree::
    :maxdepth: 1
    :caption: API Reference

    apis/xrfeitoria.rst
    apis/factory.rst
    apis/object.rst
    apis/actor.rst
    apis/camera.rst
    apis/sequence.rst
    apis/renderer.rst
    apis/utils.rst
    apis/data_structure.rst

----

.. toctree::
    :maxdepth: 1
    :caption: Plugins

    src/blender-addon.md
    src/unreal-plugin.md

--------

.. toctree::
    :maxdepth: 2
    :caption: FAQ

    faq.rst
