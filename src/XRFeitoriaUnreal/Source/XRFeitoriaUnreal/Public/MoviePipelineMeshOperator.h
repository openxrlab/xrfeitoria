// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "MoviePipeline.h"
#include "MoviePipelineOutputSetting.h"
#include "MoviePipelineMasterConfig.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformFilemanager.h"

#if WITH_EDITOR
#include "MovieSceneExportMetadata.h"
#include "MovieSceneToolHelpers.h"
#include "MovieScene.h"
#endif

#include "SequencerTools.h"
#include "SequencerSettings.h"
#include "SequencerBindingProxy.h"
#include "SequencerScriptingRange.h"

#include "Kismet/KismetMathLibrary.h"
#include "Kismet/KismetStringLibrary.h"

#include "LevelSequence.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"

#include "CoreMinimal.h"
#include "MoviePipelineOutputBase.h"
#include "MovieRenderPipelineDataTypes.h"
#include "MoviePipelineMeshOperator.generated.h"

/**
 *
 */

USTRUCT(BlueprintType)
struct XRFEITORIAUNREAL_API FMeshOperatorOption
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		bool bEnabled = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		bool bSaveVerticesPosition = true;
	//UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
	//	bool bSaveOcclusionResult = true;
	//UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
	//	bool bSaveOcclusionRate = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		FString DirectoryVertices = "vertices";
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		int32 LODIndex = 0;
};


USTRUCT(BlueprintType)
struct XRFEITORIAUNREAL_API FSkeletalMeshOperatorOption
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		bool bEnabled = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		bool bSaveVerticesPosition = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		bool bSaveSkeletonPosition = true;
	//UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
	//	bool bSaveOcclusionResult = true;
	//UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
	//	bool bSaveOcclusionRate = true;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		FString DirectoryVertices = "vertices";
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		FString DirectorySkeleton = "skeleton";
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Occlusion Checker")
		int32 LODIndex = 0;
};

UCLASS(Blueprintable)
class XRFEITORIAUNREAL_API UMoviePipelineMeshOperator : public UMoviePipelineOutputBase
{
	GENERATED_BODY()
public:
#if WITH_EDITOR
	virtual FText GetDisplayText() const override { return NSLOCTEXT("MovieRenderPipeline", "MeshOperator_DisplayText", "Mesh Operator"); }
#endif
	virtual void SetupForPipelineImpl(UMoviePipeline* InPipeline);
	virtual void OnReceiveImageDataImpl(FMoviePipelineMergerOutputFrame* InMergedOutputFrame) override;
	virtual void BeginExportImpl() override;
private:
	FString GetOutputPath(FString PassName, FString Ext, const FMoviePipelineFrameOutputState* InOutputState);

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mesh Operator")
		FMeshOperatorOption StaticMeshOperatorOption = FMeshOperatorOption();
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mesh Operator")
		FSkeletalMeshOperatorOption SkeletalMeshOperatorOption = FSkeletalMeshOperatorOption();

private:
	TMap<FString, UStaticMeshComponent*> StaticMeshComponents;
	TMap<FString, USkeletalMeshComponent*> SkeletalMeshComponents;
	bool bIsFirstFrame = true;
};
