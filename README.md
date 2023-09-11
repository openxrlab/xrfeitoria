<br/>

<div align="center">
    <img src="resources/xrfeitoria-logo.png" width="600"/>
</div>

<br/>

[![Documentation](https://readthedocs.org/projects/xrfeitoria/badge/?version=latest)](https://xrfeitoria.readthedocs.io/en/latest/?badge=latest)
[![actions](https://github.com/openxrlab/xrfeitoria/workflows/build/badge.svg)](https://github.com/openxrlab/xrfeitoria/actions)
[![codecov](https://codecov.io/gh/openxrlab/xrfeitoria/branch/main/graph/badge.svg)](https://codecov.io/gh/openxrlab/xrfeitoria)
[![PyPI](https://img.shields.io/pypi/v/xrfeitoria)](https://pypi.org/project/xrfeitoria/)
[![Percentage of issues still open](https://isitmaintained.com/badge/open/openxrlab/xrfeitoria.svg)](https://github.com/openxrlab/xrfeitoria/issues)
[![license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

## Introduction

XRFeitoria is a rendering toolbox for generating synthetic data photorealistic with ground-truth annotations.
It is a part of the [OpenXRLab](https://openxrlab.org.cn/) project.

<div align="center">
    <img src="http://file.bj.zoe.sensetime.com/resources/meihaiyi/xrfeitoria/pics/demo.gif"/>
</div>

### Major Features

- Support rendering photorealistic images with ground-truth annotations.
- Support multiple engine backends, including [Unreal Engine](https://www.unrealengine.com/) and [Blender](https://www.blender.org/).
- Support assets/camera management, including import, export, and delete.
- Support a CLI tool to render images from a mesh file.

## Installation

```bash
pip install xrfeitoria
```

### Requirements

- `Python >= 3.8`
- (optional) `Unreal Engine >= 5.1`
    - [x] Windows
    - [ ] Linux
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

### Tutorials

There are several [tutorials](/tutorials/).
You can read them [here](http://file.bj.zoe.sensetime.com/resources/meihaiyi/xrfeitoria/docs/en/_build/html/src/Tutorials.html).


### Sample codes

There are several [samples](/samples/).
Please follow the instructions [here](/samples/README.md).



## :rocket: Amazing Projects Using XRFeitoria

| Project | Teaser | Engine |
| :---: | :---: | :---: |
| [Synbody: Synthetic Dataset with Layered Human Models for 3D Human Perception and Modeling](https://synbody.github.io/) | <img src="https://synbody.github.io/static/teaser.png"/> | Unreal Engine / Blender |
| [Zolly: Zoom Focal Length Correctly for Perspective-Distorted Human Mesh Reconstruction](https://wenjiawang0312.github.io/projects/zolly/) | <img src="https://github.com/WenjiaWang0312/Zolly/blob/main/assets/demo_sota.jpg?raw=true"/> | Blender |
| [SHERF: Generalizable Human NeRF from a Single Image](https://skhu101.github.io/SHERF/) | <img src="https://github.com/skhu101/SHERF/raw/main/img/SHERF_teaser.png"/> | Blender |
| [MatrixCity: A Large-scale City Dataset for City-scale Neural Rendering and Beyond](https://city-super.github.io/matrixcity/) | <img src="https://city-super.github.io/matrixcity/img/teaser.jpg"/> | Unreal Engine |
| [HumanLiff: Layer-wise 3D Human Generation with Diffusion Model](https://skhu101.github.io/HumanLiff/) | <img src="https://skhu101.github.io/HumanLiff/HumanLiff%20-%20Project%20Page_files/SHERF_teaser.png"/> | Blender |

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