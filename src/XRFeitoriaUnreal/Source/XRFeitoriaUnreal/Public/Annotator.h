// Copyright OpenXRLab 2023-2024. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

#include "LevelSequence.h"
#include "LevelSequenceActor.h"
#include "LevelSequencePlayer.h"
#include "MovieScene.h"
#include "MovieSceneBinding.h"
#include "MovieSceneBindingProxy.h"

#include "GameFramework/Actor.h"
#include "Animation/SkeletalMeshActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/StaticMeshActor.h"

#include "Annotator.generated.h"


UCLASS(Blueprintable)
class XRFEITORIAUNREAL_API AAnnotator : public AActor
{
	GENERATED_BODY()

public:
	// Sets default values for this actor's properties
	AAnnotator();
	// Initialize the Annotator
	void Initialize();
	bool IsSequenceValid(UMovieScene* MovieScene);
	void ExportCameraParameters(int FrameNumber);
	void ExportStaticMeshParameters(int FrameNumber);
	void ExportSkeletalMeshParameters(int FrameNumber);

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:
	// Called every frame
	virtual void Tick(float DeltaTime) override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		FString DirectorySequence;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		FString NameActorInfos = "actor_infos";
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		FString NameCameraParams = "camera_params";
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		FString NameVertices = "vertices";
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		FString NameSkeleton = "skeleton";

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator|Resolution")
		int Width = 1920;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator|Resolution")
		int Height = 1080;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		bool bSaveSkeletonPosition = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		bool bSaveVerticesPosition = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp, Category = "Annotator")
		int32 LODIndexToSave = 0;

private:
	ALevelSequenceActor* LevelSequenceActor;
	ULevelSequencePlayer* LevelSequencePlayer;
	TMap<FString, ACameraActor*> CameraActors;
	TMap<FString, UStaticMeshComponent*> StaticMeshComponents;
	TMap<FString, USkeletalMeshComponent*> SkeletalMeshComponents;
	bool bInitialized = false;
};
