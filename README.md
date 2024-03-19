<br/>

<div align="center">
     <a href="https://github.com/openxrlab/xrfeitoria"><img src="https://raw.githubusercontent.com/openxrlab/xrfeitoria/main/resources/xrfeitoria-logo.png" alt="XRFeitoria" width="600"/></a>
</div>

<br/>

<div align="center">

[![Documentation](https://readthedocs.org/projects/xrfeitoria/badge/?version=latest)](https://xrfeitoria.readthedocs.io/en/latest/?badge=latest)
[![actions](https://github.com/openxrlab/xrfeitoria/actions/workflows/lint.yml/badge.svg)](https://github.com/openxrlab/xrfeitoria/actions)
[![PyPI](https://img.shields.io/pypi/v/xrfeitoria)](https://pypi.org/project/xrfeitoria/)
[![license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

</div>

## Introduction

XRFeitoria is a rendering toolbox for generating synthetic data photorealistic with ground-truth annotations.
It is a part of the [OpenXRLab](https://openxrlab.org.cn/) project.

https://github.com/openxrlab/xrfeitoria/assets/35397764/1e83bcd4-ae00-4c20-8188-3fe73f7c9c01

### Major Features

- Support rendering photorealistic images with ground-truth annotations.
- Support multiple engine backends, including [Unreal Engine](https://www.unrealengine.com/) and [Blender](https://www.blender.org/).
- Support assets/camera management, including import, place, export, and delete.
- Support a CLI tool to render images from a mesh file.

## Installation

```bash
pip install xrfeitoria
```

### Requirements

- `Python >= 3.8`
- (optional) `Unreal Engine >= 5.1`
    - [x] Windows
    - [x] Linux
    - [ ] MacOS
- (optional) `Blender >= 3.0`
    - [x] Windows
    - [x] Linux
    - [x] MacOS

## Get-Started

### CLI

```bash
xf-render --help

# render a mesh file
xf-render {mesh_file}

# for example
wget https://graphics.stanford.edu/~mdfisher/Data/Meshes/bunny.obj
xf-render bunny.obj
```

https://github.com/openxrlab/xrfeitoria/assets/35397764/430a7264-9337-4327-838d-08e9a354c277

https://github.com/openxrlab/xrfeitoria/assets/35397764/9c029eb7-a8be-4d11-890e-b2499ff22caa

### Documentation

The reference documentation is available on [readthedocs](https://xrfeitoria.readthedocs.io/en/latest/).

### Tutorials

There are several [tutorials](/tutorials/).
You can read them [here](https://xrfeitoria.readthedocs.io/en/latest/src/Tutorials.html).

### Sample codes

There are several [samples](/samples/).
Please follow the instructions [here](/samples/README.md).

### Use plugins under development

Details can be found [here](https://xrfeitoria.readthedocs.io/en/latest/faq.html#how-to-use-the-plugin-of-blender-unreal-under-development).

If you want to publish plugins of your own, you can use the following command:

```powershell
# install xrfeitoria first
cd xrfeitoria
pip install .

# for instance, build plugins for Blender, UE 5.1, UE 5.2, and UE 5.3 on Windows.
# using powershell where backtick(`) is the line continuation character.
python -m xrfeitoria.utils.publish_plugins `
    -u "C:/Program Files/Epic Games/UE_5.1/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" `
    -u "C:/Program Files/Epic Games/UE_5.2/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" `
    -u "C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
```

### Frequently Asked Questions

Please refer to [FAQ](https://xrfeitoria.readthedocs.io/en/latest/faq.html).


## :rocket: Amazing Projects Using XRFeitoria

| Project | Teaser | Engine |
| :---: | :---: | :---: |
| [SynBody: Synthetic Dataset with Layered Human Models for 3D Human Perception and Modeling](https://synbody.github.io/) | <a href=https://synbody.github.io/><img src="https://synbody.github.io/static/teaser.png"></a> | Unreal Engine / Blender |
| [Zolly: Zoom Focal Length Correctly for Perspective-Distorted Human Mesh Reconstruction](https://wenjiawang0312.github.io/projects/zolly/) | <a href=https://wenjiawang0312.github.io/projects/zolly/><img src="https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/pics/zolly.jpg"></a> | Blender |
| [SHERF: Generalizable Human NeRF from a Single Image](https://skhu101.github.io/SHERF/) | <a href=https://skhu101.github.io/SHERF/><img src="https://github.com/skhu101/SHERF/raw/main/img/SHERF_teaser.png"></a> | Blender |
| [MatrixCity: A Large-scale City Dataset for City-scale Neural Rendering and Beyond](https://city-super.github.io/matrixcity/) | <a href=https://city-super.github.io/matrixcity/><img src="https://city-super.github.io/matrixcity/img/teaser.jpg"></a> | Unreal Engine |
| [HumanLiff: Layer-wise 3D Human Generation with Diffusion Model](https://skhu101.github.io/HumanLiff/) | <a href=https://skhu101.github.io/HumanLiff/><img src="https://skhu101.github.io/HumanLiff/HumanLiff%20-%20Project%20Page_files/SHERF_teaser.png"/></a> | Blender |
| [PrimDiffusion: Volumetric Primitives Diffusion for 3D Human Generation](https://frozenburning.github.io/projects/primdiffusion/) | <a href=https://frozenburning.github.io/projects/primdiffusion/><img src="https://openxrlab-share.oss-cn-hongkong.aliyuncs.com/xrfeitoria/pics/PrimDiffusion.png"></a> | Blender |

## License

The license of our codebase is Apache-2.0. Note that this license only applies to code in our library, the dependencies of which are separate and individually licensed. We would like to pay tribute to open-source implementations to which we rely on. Please be aware that using the content of dependencies may affect the license of our codebase. Refer to [LICENSE](LICENSE) to view the full license.

## Citation

If you find this project useful in your research, please consider cite:

```bibtex
@misc{xrfeitoria,
    title={OpenXRLab Synthetic Data Rendering Toolbox},
    author={XRFeitoria Contributors},
    howpublished = {\url{https://github.com/openxrlab/xrfeitoria}},
    year={2023}
}
```


## Projects in OpenXRLab

- [XRPrimer](https://github.com/openxrlab/xrprimer): OpenXRLab foundational library for XR-related algorithms.
- [XRSLAM](https://github.com/openxrlab/xrslam): OpenXRLab Visual-inertial SLAM Toolbox and Benchmark.
- [XRSfM](https://github.com/openxrlab/xrsfm): OpenXRLab Structure-from-Motion Toolbox and Benchmark.
- [XRLocalization](https://github.com/openxrlab/xrlocalization): OpenXRLab Visual Localization Toolbox and Server.
- [XRMoCap](https://github.com/openxrlab/xrmocap): OpenXRLab Multi-view Motion Capture Toolbox and Benchmark.
- [XRMoGen](https://github.com/openxrlab/xrmogen): OpenXRLab Human Motion Generation Toolbox and Benchmark.
- [XRNeRF](https://github.com/openxrlab/xrnerf): OpenXRLab Neural Radiance Field (NeRF) Toolbox and Benchmark.
- [XRFeitoria](https://github.com/openxrlab/xrfeitoria): OpenXRLab Synthetic Data Rendering Toolbox.
