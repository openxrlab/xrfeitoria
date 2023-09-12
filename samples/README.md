# Samples

## Clone

```bash
git clone https://github.com/openxrlab/xrfeitoria.git
cd xrfeitoria
```

## Setup the environment

After [installation](../README.md#Installation), configure the **executable path** of blender or unreal by executing:

```bash
python -m samples.setup
```

This will ask you to input the path of blender or unreal, download test assets, and save the configuration to `samples/config.py`.

## Blender

```bash
python -m samples.blender.01_add_shapes [-b] [--debug]
python -m samples.blender.02_add_cameras [-b] [--debug]
python -m samples.blender.03_basic_render [-b] [--debug]
python -m samples.blender.04_staticmesh_render [-b] [--debug]
python -m samples.blender.05_skeletalmesh_render [-b] [--debug]
python -m samples.blender.06_custom_usage [-b] [--debug]
```

## Unreal

```bash
python -m samples.unreal.01_add_shapes [-b] [--debug]
python -m samples.unreal.02_add_cameras [-b] [--debug]
python -m samples.unreal.03_basic_render [-b] [--debug]
python -m samples.unreal.04_staticmesh_render [-b] [--debug]
python -m samples.unreal.05_skeletalmesh_render [-b] [--debug]
python -m samples.unreal.06_custom_usage [-b] [--debug]
```

## Run it all

```bash
python -m samples.run_all [-e {unreal,blender}] [-b] [--debug]
```
