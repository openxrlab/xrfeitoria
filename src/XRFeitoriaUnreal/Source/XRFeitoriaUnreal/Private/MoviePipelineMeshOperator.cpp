// Copyright OpenXRLab 2023-2024. All Rights Reserved.

#include "MoviePipelineMeshOperator.h"
#include "XF_BlueprintFunctionLibrary.h"
#include "Engine/StaticMeshActor.h"
#include "Animation/SkeletalMeshActor.h"
#include "LevelSequenceEditorBlueprintLibrary.h"
#include "MovieSceneObjectBindingID.h"
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

	TMap<FString, FGuid> bindingMap;
	for (int idx = 0; idx < MovieScene->GetSpawnableCount(); idx++)
	{
		FMovieSceneSpawnable spawnable = MovieScene->GetSpawnable(idx);
		FGuid guid = spawnable.GetGuid();
		FString name = spawnable.GetName();

		bindingMap.Add(name, guid);
	}

	for (int idx = 0; idx < MovieScene->GetPossessableCount(); idx++)
	{
		FMovieScenePossessable possessable = MovieScene->GetPossessable(idx);
		FGuid guid = possessable.GetGuid();
		FString name = possessable.GetName();

		bindingMap.Add(name, guid);
	}

	for (TPair<FString, FGuid> pair : bindingMap)
	{
		FString name = pair.Key;
		FGuid guid = pair.Value;

		TArray<FSequencerBoundObjects> _boundObjects_ = USequencerToolsFunctionLibrary::GetBoundObjects(
			GetPipeline()->GetWorld(),
			LevelSequence,
			TArray<FMovieSceneBindingProxy>({ FSequencerBindingProxy(guid, MovieSceneSequence) }),
			FSequencerScriptingRange::FromNative(
				MovieScene->GetPlaybackRange(),
				MovieScene->GetDisplayRate()
			)
		);

		UObject* BoundObject = _boundObjects_[0].BoundObjects[0];  // only have one item
		if (BoundObject->IsA(ASkeletalMeshActor::StaticClass()))
		{
			ASkeletalMeshActor* SkeletalMeshActor = Cast<ASkeletalMeshActor>(BoundObject);
			SkeletalMeshComponents.Add(name, SkeletalMeshActor->GetSkeletalMeshComponent());
		}
		else if (BoundObject->IsA(AStaticMeshActor::StaticClass()))
		{
			AStaticMeshActor* StaticMeshActor = Cast<AStaticMeshActor>(BoundObject);
			StaticMeshComponents.Add(name, StaticMeshActor->GetStaticMeshComponent());
		}
		//else if (BoundObject->IsA(USkeletalMeshComponent::StaticClass()))
		//{
		//	USkeletalMeshComponent* SkeletalMeshComponent = Cast<USkeletalMeshComponent>(BoundObject);
		//	// check if it's already in the list
		//	bool bFound = false;
		//	for (TPair<FString, USkeletalMeshComponent*> SKMPair : SkeletalMeshComponents)
		//	{
		//		USkeletalMeshComponent* SkeletalMeshComponentInList = SKMPair.Value;
		//		if (SkeletalMeshComponentInList == SkeletalMeshComponent)
		//		{
		//			bFound = true;
		//			break;
		//		}
		//	}
		//	if (!bFound) SkeletalMeshComponents.Add(name, SkeletalMeshComponent);
		//}
		//else if (BoundObject->IsA(UStaticMeshComponent::StaticClass()))
		//{
		//	UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(BoundObject);
		//	// check if it's already in the list
		//	bool bFound = false;
		//	for (TPair<FString, UStaticMeshComponent*> SKMPair : StaticMeshComponents)
		//	{
		//		UStaticMeshComponent* StaticMeshComponentInList = SKMPair.Value;
		//		if (StaticMeshComponentInList == StaticMeshComponent)
		//		{
		//			bFound = true;
		//			break;
		//		}
		//	}
		//	if (!bFound) StaticMeshComponents.Add(name, StaticMeshComponent);
		//}
	}
}

void UMoviePipelineMeshOperator::OnReceiveImageDataImpl(FMoviePipelineMergerOutputFrame* InMergedOutputFrame)
{
	for (TPair<FString, USkeletalMeshComponent*> SKMPair : SkeletalMeshComponents)
	{
		// loop over Skeletal mesh components
		if (!SkeletalMeshOperatorOption.bEnabled) continue;

		FString MeshName = SKMPair.Key;
		USkeletalMeshComponent* SkeletalMeshComponent = SKMPair.Value;

		//// Actor in level
		//FString MeshNameFromLabel = SkeletalMeshComponent->GetOwner()->GetActorNameOrLabel();
		//// Actor spawned from sequence
		//FString MeshNameFromName = SkeletalMeshComponent->GetOwner()->GetFName().GetPlainNameString();
		//// Judge which name is correct
		//FString MeshName = MeshNameFromName.StartsWith("SkeletalMesh") ? MeshNameFromLabel : MeshNameFromName;

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
	for (TPair<FString, UStaticMeshComponent*> SKMPair : StaticMeshComponents)
	{
		// loop over static mesh components
		if (!StaticMeshOperatorOption.bEnabled) continue;

		UStaticMeshComponent* StaticMeshComponent = SKMPair.Value;
		FString MeshName = SKMPair.Key;

		//// Actor in level
		//FString MeshNameFromLabel = StaticMeshComponent->GetOwner()->GetActorNameOrLabel();
		//// Actor spawned from sequence
		//FString MeshNameFromName = StaticMeshComponent->GetOwner()->GetFName().GetPlainNameString();
		//// Judge which name is correct
		//FString MeshName = MeshNameFromName.StartsWith("StaticMesh") ? MeshNameFromLabel : MeshNameFromName;

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
