// Copyright OpenXRLab 2023-2024. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MoviePipelineDeferredPasses.h"
#include "CustomMoviePipelineDeferredPass.generated.h"

/**
 *
 */
UCLASS()
class XRFEITORIAUNREAL_API UCustomMoviePipelineDeferredPass : public UMoviePipelineDeferredPassBase
{
	GENERATED_BODY()

protected:
	virtual void SetupImpl(const MoviePipeline::FMoviePipelineRenderPassInitSettings& InPassInitSettings) override;
#if WITH_EDITOR
	virtual FText GetDisplayText() const override { return NSLOCTEXT("MovieRenderPipeline", "Custom DeferredBasePassSetting_DisplayName_Lit", "Custom Deferred Rendering"); }
#endif

};
