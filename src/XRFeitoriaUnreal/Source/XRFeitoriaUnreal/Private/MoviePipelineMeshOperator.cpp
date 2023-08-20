// Fill out your copyright notice in the Description page of Project Settings.


#include "MoviePipelineMeshOperator.h"
#include "SF_BlueprintFunctionLibrary.h"
#include "Engine/StaticMeshActor.h"
#include "Animation/SkeletalMeshActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Misc/FileHelper.h"
#include "MovieRenderPipelineCoreModule.h"  // For logs


void UMoviePipelineMeshOperator::SetupForPipelineImpl(UMoviePipeline* InPipeline)
{
	if (InPipeline)
	{
		InPipeline->SetFlushDiskWritesPerShot(true);
	}

	ULevelSequence* LevelSequence = GetPipeline()->GetTargetSequence();
	UMovieSceneSequence* MovieSceneSequence = GetPipeline()->GetTargetSequence();
	UMovieScene* MovieScene = LevelSequence->GetMovieScene();
	TArray<FMovieSceneBinding> bindings = MovieScene->GetBindings();

	TArray<FSequencerBindingProxy> bindingProxies;
	for (FMovieSceneBinding binding : bindings)
	{
		FGuid guid = binding.GetObjectGuid();
		bindingProxies.Add(FSequencerBindingProxy(guid, MovieSceneSequence));
	}

	boundObjects = USequencerToolsFunctionLibrary::GetBoundObjects(
		GetPipeline()->GetWorld(),
		LevelSequence,
		bindingProxies,
		FSequencerScriptingRange::FromNative(
			MovieScene->GetPlaybackRange(),
			MovieScene->GetDisplayRate()
		)
	);

	for (FSequencerBoundObjects boundObject : boundObjects)
	{
		// loop over bound objects
		UObject* BoundObject = boundObject.BoundObjects[0];  // only have one item
		if (BoundObject->IsA(ASkeletalMeshActor::StaticClass()))
		{
			ASkeletalMeshActor* SkeletalMeshActor = Cast<ASkeletalMeshActor>(BoundObject);
			SkeletalMeshComponents.Add(SkeletalMeshActor->GetSkeletalMeshComponent());
		}
		else if (BoundObject->IsA(AStaticMeshActor::StaticClass()))
		{
			AStaticMeshActor* StaticMeshActor = Cast<AStaticMeshActor>(BoundObject);
			StaticMeshComponents.Add(StaticMeshActor->GetStaticMeshComponent());
		}
		else if (BoundObject->IsA(USkeletalMeshComponent::StaticClass()))
		{
			USkeletalMeshComponent* SkeletalMeshComponent = Cast<USkeletalMeshComponent>(BoundObject);
			// check if it's already in the list
			bool bFound = false;
			for (USkeletalMeshComponent* SkeletalMeshComponentInList : SkeletalMeshComponents)
			{
				if (SkeletalMeshComponentInList == SkeletalMeshComponent)
				{
					bFound = true;
					break;
				}
			}
			if (!bFound)
				SkeletalMeshComponents.Add(SkeletalMeshComponent);
			// TODO: save bone name here
		}
		else if (BoundObject->IsA(UStaticMeshComponent::StaticClass()))
		{
			UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(BoundObject);
			// check if it's already in the list
			bool bFound = false;
			for (UStaticMeshComponent* StaticMeshComponentInList : StaticMeshComponents)
			{
				if (StaticMeshComponentInList == StaticMeshComponent)
				{
					bFound = true;
					break;
				}
			}
			if (!bFound)
				StaticMeshComponents.Add(StaticMeshComponent);
		}
		else if (BoundObject->IsA(ACameraActor::StaticClass()))
		{
			Camera = Cast<ACameraActor>(BoundObject);
		}
	}
}

void UMoviePipelineMeshOperator::OnReceiveImageDataImpl(FMoviePipelineMergerOutputFrame* InMergedOutputFrame)
{
	if (bIsFirstFrame)
	{
		UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UMoviePipelineOutputSetting>();
		check(OutputSettings);
		int ResolutionX = OutputSettings->OutputResolution.X;
		int ResolutionY = OutputSettings->OutputResolution.Y;
		FVector CamLocation = Camera->GetActorLocation();
		FRotator CamRotation = Camera->GetActorRotation();
		float FOV = Camera->GetCameraComponent()->FieldOfView;

		TArray<float> CamInfo;
		CamInfo.Add(CamLocation.X);
		CamInfo.Add(CamLocation.Y);
		CamInfo.Add(CamLocation.Z);
		CamInfo.Add(CamRotation.Roll);
		CamInfo.Add(CamRotation.Pitch);
		CamInfo.Add(CamRotation.Yaw);
		CamInfo.Add(FOV);
		CamInfo.Add(ResolutionX);
		CamInfo.Add(ResolutionY);

		FString CameraTransformPath = GetOutputPath("CameraTransform", "dat", &InMergedOutputFrame->FrameOutputState);
		CameraTransformPath = FPaths::SetExtension(FPaths::GetPath(CameraTransformPath), FPaths::GetExtension(CameraTransformPath));  // get rid of the frame index
		USF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(CamInfo, CameraTransformPath);
	}

	for (USkeletalMeshComponent* SkeletalMeshComponent : SkeletalMeshComponents)
	{
		// loop over Skeletal mesh components
		if (!SkeletalMeshOperatorOption.bEnabled) continue;

		FString MeshName = SkeletalMeshComponent->GetOwner()->GetActorNameOrLabel();

		if (SkeletalMeshOperatorOption.bSaveVerticesPosition)
		{
			// Get Vertex Positions (LOD 0)
			TArray<FVector> VertexPositions;
			bool isSuccess = USF_BlueprintFunctionLibrary::GetSkeletalMeshVertexLocationsByLODIndex(
				SkeletalMeshComponent,
				0,  // LODIndex
				VertexPositions
			);
			if (!isSuccess)
			{
				UE_LOG(LogMovieRenderPipeline, Error, TEXT("Failed to get vertex positions"));
				continue;
			}
			TArray<float> VertexPositionsFloat;
			for (FVector position : VertexPositions)
			{
				VertexPositionsFloat.Add(position.X);
				VertexPositionsFloat.Add(position.Y);
				VertexPositionsFloat.Add(position.Z);
			}
			USF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
				VertexPositionsFloat, GetOutputPath("Vertex" / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));
		}

		if (SkeletalMeshOperatorOption.bSaveOcclusionRate || SkeletalMeshOperatorOption.bSaveOcclusionResult)
		{

			float non_occlusion_rate;
			float self_occlusion_rate;
			float inter_occlusion_rate;
			TArray<FVector> SkeletonPositions;
			TArray<FName> SkeletonNames;
			TArray<EOcclusion> SkeletonOcclusion;
			float MeshThickness = 5.0f;
			bool isSuccess = USF_BlueprintFunctionLibrary::DetectInterOcclusionSkeleton(
				SkeletalMeshComponent,
				Camera,
				non_occlusion_rate,
				self_occlusion_rate,
				inter_occlusion_rate,
				SkeletonPositions,
				SkeletonNames,
				SkeletonOcclusion,
				MeshThickness,
				false
			);

			// Skeleton Names
			TArray<FString> SkeletonNamesString;
			for (FName name : SkeletonNames) SkeletonNamesString.Add(name.ToString());
			FString BoneNamePath = GetOutputPath("BoneNames" / MeshName, "txt", &InMergedOutputFrame->FrameOutputState);
			BoneNamePath = FPaths::SetExtension(FPaths::GetPath(BoneNamePath), FPaths::GetExtension(BoneNamePath));  // get rid of the frame index
			if (bIsFirstFrame) FFileHelper::SaveStringArrayToFile(SkeletonNamesString, *BoneNamePath);

			// Occlusion Int
			TArray<uint8> SkeletonOcclusionInt;
			for (EOcclusion occlusion : SkeletonOcclusion) SkeletonOcclusionInt.Add((uint8)occlusion);
			FFileHelper::SaveArrayToFile(
				SkeletonOcclusionInt, *GetOutputPath("Occlusion" / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));

			// Occlusion rate
			TArray<float> OcclusionRate;
			OcclusionRate.Add(non_occlusion_rate);
			OcclusionRate.Add(self_occlusion_rate);
			OcclusionRate.Add(inter_occlusion_rate);
			USF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
				OcclusionRate, *GetOutputPath("OcclusionRate" / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));

			// Skeleton Positions
			TArray<float> SkeletonPositionsFloat;
			for (FVector position : SkeletonPositions)
			{
				SkeletonPositionsFloat.Add(position.X);
				SkeletonPositionsFloat.Add(position.Y);
				SkeletonPositionsFloat.Add(position.Z);
			}
			USF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
				SkeletonPositionsFloat, GetOutputPath("SkeletonPositions" / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));


			// TODO: export to npz
		}

	}

	// TODO: add static mesh components
	if (bIsFirstFrame) bIsFirstFrame = false;
}


void UMoviePipelineMeshOperator::BeginExportImpl()
{
	FCoreDelegates::OnEndFrame.RemoveAll(this);
	UE_LOG(LogMovieRenderPipelineIO, Log, TEXT("Mesh Operator Ended."));
}

FString UMoviePipelineMeshOperator::GetOutputPath(FString PassName, FString Ext, const FMoviePipelineFrameOutputState* InOutputState)
{
	UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UMoviePipelineOutputSetting>();
	check(OutputSettings);
	FString OutputDirectory = OutputSettings->OutputDirectory.Path;
	FString FileNameFormatString = OutputSettings->FileNameFormat;

	FString OutputPath;
	FMoviePipelineFormatArgs Args;
	TMap<FString, FString> FormatOverrides;
	FormatOverrides.Add(TEXT("render_pass"), PassName);
	FormatOverrides.Add(TEXT("ext"), Ext);
	GetPipeline()->ResolveFilenameFormatArguments(
		OutputDirectory / FileNameFormatString, FormatOverrides, OutputPath, Args, InOutputState);

	return OutputPath;
}
