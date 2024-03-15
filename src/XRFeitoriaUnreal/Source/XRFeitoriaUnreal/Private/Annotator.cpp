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

	// Get All Bound Objects
	const TArray<FMovieSceneBinding>& ObjectBindings = LevelSequence->GetMovieScene()->GetBindings();
	TArray<FMovieSceneBindingProxy> bindingProxies;
	for (FMovieSceneBinding binding : ObjectBindings)
	{
		FGuid guid = binding.GetObjectGuid();
		bindingProxies.Add(FSequencerBindingProxy(guid, LevelSequence));
	}
	TArray<FSequencerBoundObjects> boundObjects = USequencerToolsFunctionLibrary::GetBoundObjects(
		GetWorld(),
		LevelSequence,
		bindingProxies,
		FSequencerScriptingRange::FromNative(
			LevelSequence->GetMovieScene()->GetPlaybackRange(),
			LevelSequence->GetMovieScene()->GetDisplayRate()
		)
	);
	UE_LOG(LogXF, Log, TEXT("Detected %d bound objects"), boundObjects.Num());

	// Get CameraActors, StaticMeshComponents, SkeletalMeshComponents from LevelSequence
	for (FSequencerBoundObjects boundObject : boundObjects)
	{
		// loop over bound objects
		UObject* BoundObject = boundObject.BoundObjects[0];  // only have one item
		if (BoundObject->IsA(ACameraActor::StaticClass()))
		{
			ACameraActor* Camera = Cast<ACameraActor>(BoundObject);
			CameraActors.Add(Camera);
		}
		else if (BoundObject->IsA(ASkeletalMeshActor::StaticClass()))
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
	UE_LOG(LogXF, Log, TEXT("Detected %d CameraActors, %d StaticMeshComponents, %d SkeletalMeshComponents"),
				CameraActors.Num(), StaticMeshComponents.Num(), SkeletalMeshComponents.Num());

	// Save Skeleton Names (only save on the first frame)
	if (bSaveSkeletonPosition)
	{
		for (USkeletalMeshComponent* SkeletalMeshComponent : SkeletalMeshComponents)
		{
			FString MeshName = SkeletalMeshComponent->GetOwner()->GetFName().GetPlainNameString();
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
				DirectorySkeleton,
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
	for (ACameraActor* Camera : CameraActors)
	{
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
			DirectoryCameraParams,  // camera_params
			Camera->GetFName().GetPlainNameString(),  // camera_name
			FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"  // frame_idx
		);  // {seq_dir}/{camera_params}/{camera_name}/{frame_idx}.dat
		UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(CamInfo, CameraTransformPath);
	}
}

void AAnnotator::ExportStaticMeshParameters(int FrameNumber)
{
	for (UStaticMeshComponent* StaticMeshComponent : StaticMeshComponents)
	{
		FString MeshName = StaticMeshComponent->GetOwner()->GetFName().GetPlainNameString();

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
				DirectoryActorParams,
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
					DirectoryVertices,
					MeshName,
					FString::Printf(TEXT("%04d"), FrameNumber) + ".dat"
				)
			);
		}
	}
}

void AAnnotator::ExportSkeletalMeshParameters(int FrameNumber)
{
	for (USkeletalMeshComponent* SkeletalMeshComponent : SkeletalMeshComponents)
	{
		FString MeshName = SkeletalMeshComponent->GetOwner()->GetFName().GetPlainNameString();

		// Save Actor Info (location, rotation, stencil value)
		{
			FVector ActorLocation = SkeletalMeshComponent->GetOwner()->GetActorLocation();
			FRotator ActorRotation = SkeletalMeshComponent->GetOwner()->GetActorRotation();
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
				DirectoryActorParams,
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
					DirectoryVertices,
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
					DirectorySkeleton,
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
