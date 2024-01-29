// Copyright OpenXRLab 2023-2024. All Rights Reserved.

#include "CustomMoviePipelineDeferredPass.h"
#include "CustomMoviePipelineOutput.h"

void UCustomMoviePipelineDeferredPass::SetupImpl(const MoviePipeline::FMoviePipelineRenderPassInitSettings& InPassInitSettings)
{

	#if ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION <2
		UCustomMoviePipelineOutput* OutputSettings = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UCustomMoviePipelineOutput>();
	#else
		UCustomMoviePipelineOutput* OutputSettings = GetPipeline()->GetPipelinePrimaryConfig()->FindSetting<UCustomMoviePipelineOutput>();
	#endif
	check(OutputSettings);

	AdditionalPostProcessMaterials.Empty();
	for (FCustomMoviePipelineRenderPass& Pass : OutputSettings->AdditionalRenderPasses)
	{
		if (Pass.Material.IsNull() || Pass.bEnabled == false)
		{
			continue;
		}
		FMoviePipelinePostProcessPass NewPass;
		NewPass.bEnabled = Pass.bEnabled;
		NewPass.Material = Pass.Material;
		AdditionalPostProcessMaterials.Add(NewPass);

		FString PassName = Pass.Material.LoadSynchronous()->GetName();
		Pass.SPassName = PassIdentifier.Name + PassName;  // set identifier pass name
		if (Pass.RenderPassName.IsEmpty())
		{
			Pass.RenderPassName = PassName;
		}
	}

	UE_LOG(LogMovieRenderPipeline, Log, TEXT("Custom Movie Pipeline Finished, %d ppm materials."), AdditionalPostProcessMaterials.Num());

	Super::SetupImpl(InPassInitSettings);
}
