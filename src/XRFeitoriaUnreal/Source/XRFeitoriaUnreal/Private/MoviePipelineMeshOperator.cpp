// Fill out your copyright notice in the Description page of Project Settings.


#include "MoviePipelineMeshOperator.h"
#include "XF_BlueprintFunctionLibrary.h"
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

	TArray<FMovieSceneBindingProxy> bindingProxies;
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
			if (!bFound) SkeletalMeshComponents.Add(SkeletalMeshComponent);
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
	}
}

void UMoviePipelineMeshOperator::OnReceiveImageDataImpl(FMoviePipelineMergerOutputFrame* InMergedOutputFrame)
{
	for (USkeletalMeshComponent* SkeletalMeshComponent : SkeletalMeshComponents)
	{
		// loop over Skeletal mesh components
		if (!SkeletalMeshOperatorOption.bEnabled) continue;

		// Actor in level
		FString MeshNameFromLabel = SkeletalMeshComponent->GetOwner()->GetActorNameOrLabel();
		// Actor spawned from sequence
		FString MeshNameFromName = SkeletalMeshComponent->GetOwner()->GetFName().GetPlainNameString();
		// Judge which name is correct
		FString MeshName = MeshNameFromName.StartsWith("SkeletalMesh") ? MeshNameFromLabel : MeshNameFromName;

		if (SkeletalMeshOperatorOption.bSaveVerticesPosition)
		{
			// Get Vertex Positions (with LOD)
			TArray<FVector> VertexPositions;
			bool isSuccess = UXF_BlueprintFunctionLibrary::GetSkeletalMeshVertexLocationsByLODIndex(
				SkeletalMeshComponent,
				SkeletalMeshOperatorOption.LODIndex,
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
			UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
				VertexPositionsFloat, GetOutputPath(
					SkeletalMeshOperatorOption.DirectoryVertices / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));
		}

		if (SkeletalMeshOperatorOption.bSaveSkeletonPosition)
		{
			TArray<FVector> SkeletonPositions;
			TArray<FName> SkeletonNames;
			bool isSuccess = UXF_BlueprintFunctionLibrary::GetSkeletalMeshBoneLocations(
				SkeletalMeshComponent, SkeletonPositions, SkeletonNames);

			// Skeleton Names (only save on the first frame)
			TArray<FString> SkeletonNamesString;
			for (FName name : SkeletonNames) SkeletonNamesString.Add(name.ToString());
			FString BoneNamePath = GetOutputPath(
				SkeletalMeshOperatorOption.DirectorySkeleton / MeshName, "txt", &InMergedOutputFrame->FrameOutputState);
			// save to DirectorySkeleton / BoneName.txt
			BoneNamePath = FPaths::Combine(
				FPaths::GetPath(BoneNamePath),
				FPaths::SetExtension("BoneName", FPaths::GetExtension(BoneNamePath))
			);
			if (bIsFirstFrame) FFileHelper::SaveStringArrayToFile(SkeletonNamesString, *BoneNamePath);

			// Skeleton Positions
			TArray<float> SkeletonPositionsFloat;
			for (FVector position : SkeletonPositions)
			{
				SkeletonPositionsFloat.Add(position.X);
				SkeletonPositionsFloat.Add(position.Y);
				SkeletonPositionsFloat.Add(position.Z);
			}
			UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
				SkeletonPositionsFloat, GetOutputPath(
					SkeletalMeshOperatorOption.DirectorySkeleton / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));
		}

		//if (SkeletalMeshOperatorOption.bSaveOcclusionRate || SkeletalMeshOperatorOption.bSaveOcclusionResult)
		//{
		//
		//	float non_occlusion_rate;
		//	float self_occlusion_rate;
		//	float inter_occlusion_rate;
		//	TArray<FVector> SkeletonPositions;
		//	TArray<FName> SkeletonNames;
		//	TArray<EOcclusion> SkeletonOcclusion;
		//	float MeshThickness = 5.0f;
		//	bool isSuccess = UXF_BlueprintFunctionLibrary::DetectInterOcclusionSkeleton(
		//		SkeletalMeshComponent,
		//		Camera,
		//		non_occlusion_rate,
		//		self_occlusion_rate,
		//		inter_occlusion_rate,
		//		SkeletonPositions,
		//		SkeletonNames,
		//		SkeletonOcclusion,
		//		MeshThickness,
		//		false
		//	);
		//	// Occlusion Int
		//	TArray<uint8> SkeletonOcclusionInt;
		//	for (EOcclusion occlusion : SkeletonOcclusion) SkeletonOcclusionInt.Add((uint8)occlusion);
		//	FFileHelper::SaveArrayToFile(
		//		SkeletonOcclusionInt, *GetOutputPath("Occlusion" / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));
		//
		//	// Occlusion rate
		//	TArray<float> OcclusionRate;
		//	OcclusionRate.Add(non_occlusion_rate);
		//	OcclusionRate.Add(self_occlusion_rate);
		//	OcclusionRate.Add(inter_occlusion_rate);
		//	UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
		//		OcclusionRate, *GetOutputPath("OcclusionRate" / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));
		//	// TODO: export to npz
		//}
	}
	for (UStaticMeshComponent* StaticMeshComponent : StaticMeshComponents)
	{
		// loop over static mesh components
		if (!StaticMeshOperatorOption.bEnabled) continue;

		// Actor in level
		FString MeshNameFromLabel = StaticMeshComponent->GetOwner()->GetActorNameOrLabel();
		// Actor spawned from sequence
		FString MeshNameFromName = StaticMeshComponent->GetOwner()->GetFName().GetPlainNameString();
		// Judge which name is correct
		FString MeshName = MeshNameFromName.StartsWith("StaticMesh") ? MeshNameFromLabel : MeshNameFromName;

		if (StaticMeshOperatorOption.bSaveVerticesPosition)
		{
			// Get Vertex Positions (with LOD)
			TArray<FVector> VertexPositions;
			bool isSuccess = UXF_BlueprintFunctionLibrary::GetStaticMeshVertexLocations(
				StaticMeshComponent,
				StaticMeshOperatorOption.LODIndex,
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
			UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
				VertexPositionsFloat, GetOutputPath(
					StaticMeshOperatorOption.DirectoryVertices / MeshName, "dat", &InMergedOutputFrame->FrameOutputState));
		}
	}
	if (bIsFirstFrame) bIsFirstFrame = false;
}


void UMoviePipelineMeshOperator::BeginExportImpl()
{
	FCoreDelegates::OnEndFrame.RemoveAll(this);
	UE_LOG(LogMovieRenderPipelineIO, Log, TEXT("Mesh Operator Ended."));
}

FString UMoviePipelineMeshOperator::GetOutputPath(FString PassName, FString Ext, const FMoviePipelineFrameOutputState* InOutputState)
{
	//UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelinePrimaryConfig()->FindSetting<UMoviePipelineOutputSetting>();
	UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UMoviePipelineOutputSetting>();
	check(OutputSettings);
	FString OutputDirectory = OutputSettings->OutputDirectory.Path;
	FString FileNameFormatString = OutputSettings->FileNameFormat;

	FString OutputPath;
	FMoviePipelineFormatArgs Args;
	TMap<FString, FString> FormatOverrides;
	FormatOverrides.Add(TEXT("camera_name"), "");
	FormatOverrides.Add(TEXT("render_pass"), PassName);
	FormatOverrides.Add(TEXT("ext"), Ext);
	GetPipeline()->ResolveFilenameFormatArguments(
		OutputDirectory / FileNameFormatString, FormatOverrides, OutputPath, Args, InOutputState);

	if (FPaths::IsRelative(OutputPath))
	{
		OutputPath = FPaths::ConvertRelativePathToFull(OutputPath);
	}

	// Replace any double slashes with single slashes.
	OutputPath.ReplaceInline(TEXT("//"), TEXT("/"));

	return OutputPath;
}
