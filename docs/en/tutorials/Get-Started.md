# Get Started

## Install `Unreal Engine`

### Download and Install Epic Games Launcher

[https://store.epicgames.com/en-US/download](https://store.epicgames.com/en-US/download)

### Install `Unreal Engine 5.0.3` in Epic Games Launcher

![EpicGameLauncher](../pics/EpicGameLauncher.png "EpicGameLauncher")

Choose `Unreal Engine 5.0.3` and click `Install` in your own setting 
(normally default setting is good).

## Run demonstration

```bash
python misc/run_cmd_async.py -f misc/user.json
```

You can simply run the command above to run a demonstration which contains:
- generating a sequence containing a `render people` model with animations and a `cube`
- rendering to RGB, mask, depth, normal map, and optical flow.

**The rendering results are saved in `Output_Path` defined in `render_config.yaml`.**
- visualize the results in `Output_Path`
<!-- - use [visualize.py](../misc/visualize.py) or  -->
<!-- [exr_reader.py](https://github.com/openxrlab/xrprimer/blob/main/python/xrprimer/io/exr_reader.py) -->
<!-- to convert `.exr` results to `.png`, for example: -->

```bash
$Output_Path="E:\Datasets\tmp"
python misc/visualize.py -i $Output_Path -o $Output_Path/vis_mask --img_pattern "*/mask/*" -t mask 
python misc/visualize.py -i $Output_Path -o $Output_Path/vis_depth --img_pattern "*/depth/*" -t depth 
python misc/visualize.py -i $Output_Path -o $Output_Path/vis_flow --img_pattern "*/flow/*" -t flow 
```

You would get a result like:

![demo](../pics/demo.gif)

<!-- **For details of this demonstration, please refer to [Tutorial](./Tutorial.md).** -->

---

> This plugin will automatically set some project settings for ue project (see [Source/XRFeitoriaUnreal/Private/XRFeitoriaUnreal.cpp](../../../src/XRFeitoriaUnreal/Source/XRFeitoriaUnreal/Private/XRFeitoriaUnreal.cpp) for details):
> 
> - `URendererSettings->CustomDepthStencil = ECustomDepthStencil::EnabledWithStencil`
> (same as `r.CustomDepth=3` in `Config/DefaultEngine.ini` under `[/Script/Engine.RendererSettings]`
> 
> - `URendererSettings->VelocityPass = EVelocityOutputPass::BasePass`
> (same as `r.VelocityOutputPass=1` in `Config/DefaultEngine.ini` under `[/Script/Engine.RendererSettings]`)
> 
>     - in UE 4.27: `Settings->bBasePassOutputsVelocity = True` 
>    (same as `r.BasePassOutputsVelocity=True` in `Config/DefaultEngine.ini` under `[/Script/Engine.RendererSettings]`)
> 
> - `UMovieRenderPipelineProjectSettings->DefaultClasses.Add(UCustomMoviePipelineOutput::StaticClass());`
> `UMovieRenderPipelineProjectSettings->DefaultClasses.Add(UCustomMoviePipelineDeferredPass::StaticClass());`
> ![movie render pipeline setting](../pics/MovieRenderPipelineProjectSettings.png "Movie Render Pipeline Setting")