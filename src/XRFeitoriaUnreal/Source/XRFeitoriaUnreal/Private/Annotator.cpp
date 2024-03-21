// Copyright OpenXRLab 2023-2024. All Rights Reserved.

#include "Annotator.h"

#include "SequencerBindingProxy.h"
#include "SequencerScriptingRange.h"
#include "SequencerSettings.h"
#include "SequencerTools.h"

#include "EngineUtils.h"
#include "XF_BlueprintFunctionLibrary.h"


// Sets default values
AAnnotator::AAnnotator()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

void AAnnotator::Initialize()
{
	if (bInitialized) return;

	// Get Playing LevelSequenceActor
	for (TActorIterator<ALevelSequenceActor> ActorItr(GetWorld()); ActorItr; ++ActorItr)
	{
		ALevelSequenceActor* ALevelSequenceActor = *ActorItr;
		bool bValid = ALevelSequenceActor && ALevelSequenceActor->GetSequencePlayer() && ALevelSequenceActor->GetSequencePlayer()->IsPlaying();
		if (!bValid) return;

		LevelSequenceActor = ALevelSequenceActor;
		LevelSequencePlayer = ALevelSequenceActor->GetSequencePlayer();
		UE_LOG(LogXF, Log, TEXT("Detected LevelSequenceActor: %s"), *LevelSequenceActor->GetName());
	}
	ULevelSequence* LevelSequence = LevelSequenceActor->GetSequence();
	UMovieScene* MovieScene = LevelSequence->GetMovieScene();

	// Get All Bound Objects
	TMap<FString, UObject*> BoundObjects;
	for (int idx = 0; idx < MovieScene->GetSpawnableCount(); idx++)
	{
		FMovieSceneSpawnable spawnable = MovieScene->GetSpawnable(idx);
		FGuid guid = spawnable.GetGuid();
		FString name = spawnable.GetName();

		TArray<UObject*> boundObjects = LevelSequencePlayer->GetBoundObjects(FMovieSceneObjectBindingID(guid));
		if (boundObjects.Num() == 0) continue;
		BoundObjects.Add(name, boundObjects[0]);
	}
	for (int idx = 0; idx < MovieScene->GetPossessableCount(); idx++)
	{
		FMovieScenePossessable possessable = MovieScene->GetPossessable(idx);
		FGuid guid = possessable.GetGuid();
		FString name = possessable.GetName();

		TArray<UObject*> boundObjects = LevelSequencePlayer->GetBoundObjects(FMovieSceneObjectBindingID(guid));
		if (boundObjects.Num() == 0) continue;
		BoundObjects.Add(name, boundObjects[0]);
	}
	UE_LOG(LogXF, Log, TEXT("Detected %d bound objects"), BoundObjects.Num());

	// Get CameraActors, StaticMeshComponents, SkeletalMeshComponents from LevelSequence
	for (TPair<FString, UObject*> pair : BoundObjects)
	{
		FString name = pair.Key;
		UObject* BoundObject = pair.Value;

		// loop over bound objects
		if (BoundObject->IsA(ACameraActor::StaticClass()))
		{
			ACameraActor* Camera = Cast<ACameraActor>(BoundObject);
			CameraActors.Add(name, Camera);
		}
		else if (BoundObject->IsA(ASkeletalMeshActor::StaticClass()))
		{
			ASkeletalMeshActor* SkeletalMeshActor = Cast<ASkeletalMeshActor>(BoundObject);
			SkeletalMeshComponents.Add(name, SkeletalMeshActor->GetSkeletalMeshComponent());
		}
		else if (BoundObject->IsA(AStaticMeshActor::StaticClass()))
		{
			AStaticMeshActor* StaticMeshActor = Cast<AStaticMeshActor>(BoundObject);
			StaticMeshComponents.Add(name, StaticMeshActor->GetStaticMeshComponent());
		}
	}
	UE_LOG(LogXF, Log, TEXT("Detected %d CameraActors, %d StaticMeshComponents, %d SkeletalMeshComponents"),
				CameraActors.Num(), StaticMeshComponents.Num(), SkeletalMeshComponents.Num());

	// Save Skeleton Names (only save on the first frame)
	if (bSaveSkeletonPosition)
	{
		for (TPair<FString, USkeletalMeshComponent*> pair : SkeletalMeshComponents)
		{
			FString MeshName = pair.Key;
			USkeletalMeshComponent* SkeletalMeshComponent = pair.Value;

			TArray<FVector> SkeletonPositions;
			TArray<FName> SkeletonNames;
			bool isSuccess = UXF_BlueprintFunctionLibrary::GetSkeletalMeshBoneLocations(
				SkeletalMeshComponent, SkeletonPositions, SkeletonNames);

			if (!isSuccess)
			{
				UE_LOG(LogMovieRenderPipeline, Error, TEXT("Failed to get skeleton positions"));
				continue;
			}

			TArray<FString> SkeletonNamesString;
			for (FName name : SkeletonNames) SkeletonNamesString.Add(name.ToString());
			FString BoneNamePath = FPaths::Combine(
				DirectorySequence,
				NameSkeleton,
				MeshName + "_BoneName.txt"
			);  // {seq_dir}/{skeleton}/{actor_name}_BoneName.txt
			FFileHelper::SaveStringArrayToFile(SkeletonNamesString, *BoneNamePath);
		}
	}

	// Finish Initialization
	bInitialized = true;
}

void AAnnotator::ExportCameraParameters(int FrameNumber)
{
	if (!bInitialized || CameraActors.Num() == 0) return;
	for (TPair<FString, ACameraActor*> pair : CameraActors)
	{
		FString CameraName = pair.Key;
		ACameraActor* Camera = pair.Value;

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
		CamInfo.Add(Width);
		CamInfo.Add(Height);

		FString CameraTransformPath = FPaths::Combine(
			DirectorySequence,  // seq_dir
			NameCameraParams,  // camera_params
			CameraName,  // camera_name
			FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"  // frame_idx
		);  // {seq_dir}/{camera_params}/{camera_name}/{frame_idx}.dat
		UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(CamInfo, CameraTransformPath);
	}
}

void AAnnotator::ExportStaticMeshParameters(int FrameNumber)
{
	for (TPair<FString, UStaticMeshComponent*> pair : StaticMeshComponents)
	{
		FString MeshName = pair.Key;
		UStaticMeshComponent* StaticMeshComponent = pair.Value;

		// Save Actor Info (location, rotation, stencil value)
		{
			FVector ActorLocation = StaticMeshComponent->GetOwner()->GetActorLocation();
			FRotator ActorRotation = StaticMeshComponent->GetOwner()->GetActorRotation();
			int StencilValue = StaticMeshComponent->CustomDepthStencilValue;

			TArray<float> ActorInfo;
			ActorInfo.Add(ActorLocation.X);
			ActorInfo.Add(ActorLocation.Y);
			ActorInfo.Add(ActorLocation.Z);
			ActorInfo.Add(ActorRotation.Roll);
			ActorInfo.Add(ActorRotation.Pitch);
			ActorInfo.Add(ActorRotation.Yaw);
			ActorInfo.Add(StencilValue);

			FString ActorInfoPath = FPaths::Combine(
				DirectorySequence,
				NameActorInfos,
				MeshName,
				FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"
			);  // {seq_dir}/{actor_params}/{actor_name}/{frame_idx}.dat
			UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(ActorInfo, ActorInfoPath);
		}

		// Save Vertex Positions
		if (bSaveVerticesPosition)
		{
			// Get Vertex Positions
			TArray<FVector> VertexPositions;
			bool isSuccess = UXF_BlueprintFunctionLibrary::GetStaticMeshVertexLocations(StaticMeshComponent, LODIndexToSave, VertexPositions);
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
				VertexPositionsFloat,
				FPaths::Combine(
					DirectorySequence,
					NameVertices,
					MeshName,
					FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"
				)
			);
		}
	}
}

void AAnnotator::ExportSkeletalMeshParameters(int FrameNumber)
{
	for (TPair<FString, USkeletalMeshComponent*> pair : SkeletalMeshComponents)
	{
		FString MeshName = pair.Key;
		USkeletalMeshComponent* SkeletalMeshComponent = pair.Value;

		// Save Actor Info (location, rotation, stencil value)
		{
			FTransform ActorTransform = SkeletalMeshComponent->GetOwner()->GetActorTransform();
			UXF_BlueprintFunctionLibrary::ConvertUnrealToOpenCV(ActorTransform);
			UE_LOG(LogTemp, Warning, TEXT("ActorTransform: %s"), *ActorTransform.ToString());
			FVector ActorLocation = ActorTransform.GetLocation();
			FRotator ActorRotation = ActorTransform.Rotator();
			int StencilValue = SkeletalMeshComponent->CustomDepthStencilValue;

			TArray<float> ActorInfo;
			ActorInfo.Add(ActorLocation.X);
			ActorInfo.Add(ActorLocation.Y);
			ActorInfo.Add(ActorLocation.Z);
			ActorInfo.Add(ActorRotation.Roll);
			ActorInfo.Add(ActorRotation.Pitch);
			ActorInfo.Add(ActorRotation.Yaw);
			ActorInfo.Add(StencilValue);

			FString ActorInfoPath = FPaths::Combine(
				DirectorySequence,
				NameActorInfos,
				MeshName,
				FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"
			);  // {seq_dir}/{actor_params}/{actor_name}/{frame_idx}.dat
			UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(ActorInfo, ActorInfoPath);
		}

		// Save Vertex Positions
		if (bSaveVerticesPosition)
		{
			// Get Vertex Positions (with LOD)
			TArray<FVector> VertexPositions;
			bool isSuccess = UXF_BlueprintFunctionLibrary::GetSkeletalMeshVertexLocationsByLODIndex(SkeletalMeshComponent, LODIndexToSave, VertexPositions);
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
				VertexPositionsFloat,
				FPaths::Combine(
					DirectorySequence,
					NameVertices,
					MeshName,
					FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"
				)
			);
		}

		// Save Skeleton Positions
		if (bSaveSkeletonPosition)
		{
			TArray<FVector> SkeletonPositions;
			TArray<FName> SkeletonNames;
			bool isSuccess = UXF_BlueprintFunctionLibrary::GetSkeletalMeshBoneLocations(
				SkeletalMeshComponent, SkeletonPositions, SkeletonNames);

			if (!isSuccess)
			{
				UE_LOG(LogMovieRenderPipeline, Error, TEXT("Failed to get skeleton positions"));
				continue;
			}

			// Skeleton Positions
			TArray<float> SkeletonPositionsFloat;
			for (FVector position : SkeletonPositions)
			{
				SkeletonPositionsFloat.Add(position.X);
				SkeletonPositionsFloat.Add(position.Y);
				SkeletonPositionsFloat.Add(position.Z);
			}
			UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(
				SkeletonPositionsFloat,
				FPaths::Combine(
					DirectorySequence,
					NameSkeleton,
					MeshName,
					FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"
				)
			);
		}
	}
}

// Called when the game starts or when spawned
void AAnnotator::BeginPlay()
{
	Super::BeginPlay();

}

// Called every frame
void AAnnotator::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	Initialize();
	if (!bInitialized) return;

	int FrameNum = LevelSequencePlayer->GetCurrentTime().Time.GetFrame().Value;
	ExportCameraParameters(FrameNum);
	ExportSkeletalMeshParameters(FrameNum);
	ExportStaticMeshParameters(FrameNum);
}
