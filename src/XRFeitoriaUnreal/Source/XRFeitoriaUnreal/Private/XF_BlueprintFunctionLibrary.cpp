// Fill out your copyright notice in the Description page of Project Settings.


#include "XF_BlueprintFunctionLibrary.h"


#include "iostream"
#include <fstream>
#include <assert.h>
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "Misc/MessageDialog.h"
#include "Engine/ObjectLibrary.h"
#include "EditorFramework/AssetImportData.h"
#include "GenericPlatform/GenericPlatformFile.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/MultiSizeIndexContainer.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "GameFramework/Actor.h"
#include "Math/Vector.h"
#include "Math/Rotator.h"
#include "Camera/CameraActor.h"

#include "Kismet/KismetSystemLibrary.h"
#include "Kismet/KismetStringLibrary.h"
#include "DrawDebugHelpers.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "PhysicsAssetUtils.h"
#include "PhysicsEngine/PhysicsAsset.h"

#if ENGINE_MAJOR_VERSION == 4
//~~~ PhysX ~~~
#include "PhysXIncludes.h"
#include "PhysXPublic.h"		//For the ptou conversions
#include "DSP/Chorus.h"

#elif ENGINE_MAJOR_VERSION == 5
#include "StaticMeshDescription.h"

#endif


DEFINE_LOG_CATEGORY(LogXF);


bool UXF_BlueprintFunctionLibrary::FileExists(FString Path)
{
	IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
	if (PlatformFile.FileExists(*Path))
	{
		return true;
	}
	return false;
}

bool UXF_BlueprintFunctionLibrary::SaveFloatToByteFile(float f, FString Path)
{
	if (!FPlatformFileManager::Get().GetPlatformFile().CreateDirectoryTree(*FPaths::GetPath(Path)))
	{
		return false;
	}

	std::string path = std::string(TCHAR_TO_UTF8(*Path));
	std::ofstream file;
	file.open(path, std::ios_base::binary);
	assert(file.is_open());

	file.write((char*) &f, sizeof(f));
	file.close();
	return true;
}

bool UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(TArray<float> FloatArray, FString Path)
{
	if (!FPlatformFileManager::Get().GetPlatformFile().CreateDirectoryTree(*FPaths::GetPath(Path)))
	{
		return false;
	}

	std::string path = std::string(TCHAR_TO_UTF8(*Path));
	std::ofstream file;
	file.open(path, std::ios_base::binary);
	assert(file.is_open());

	for (int idx=0; idx!=FloatArray.Num(); idx++)
	{
		file.write((char*) &FloatArray[idx], sizeof(float));
	}
	file.close();

	return true;
}


void UXF_BlueprintFunctionLibrary::EmptyPostProcessMaterial(UPostProcessComponent* postprocessComponent)
{
	postprocessComponent->Settings.WeightedBlendables.Array.Empty();
}


void UXF_BlueprintFunctionLibrary::ModifyPostProcessMaterial(UMaterialInterface * mat, UPostProcessComponent* postprocessComponent)
{
	postprocessComponent->Settings.WeightedBlendables.Array.Empty();
	if (mat != NULL)
	{
		postprocessComponent->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1., mat));
	}
}


bool UXF_BlueprintFunctionLibrary::FileIO__SaveStringTextToFile(
	FString SaveDirectory,
	FString JoyfulFileName,
	FString SaveText,
	bool AllowOverWriting,
	bool AllowAppend
){
	if(!FPlatformFileManager::Get().GetPlatformFile().CreateDirectoryTree(*SaveDirectory))
	{
		//Could not make the specified directory
		return false;
		//~~~~~~~~~~~~~~~~~~~~~~
	}

	//get complete file path
	SaveDirectory += "\\";
	SaveDirectory += JoyfulFileName;

	//No over-writing?
	if (!AllowOverWriting)
	{
		//Check if file exists already
		if (FPlatformFileManager::Get().GetPlatformFile().FileExists( * SaveDirectory))
		{
			//no overwriting
			return false;
		}
	}

	if (AllowAppend)
	{
		SaveText += "\n";
		return FFileHelper::SaveStringToFile(SaveText, * SaveDirectory,
				FFileHelper::EEncodingOptions::AutoDetect,&IFileManager::Get(), EFileWrite::FILEWRITE_Append);
	}
	return FFileHelper::SaveStringToFile(SaveText, * SaveDirectory);
}

bool UXF_BlueprintFunctionLibrary::FileIO__GetFiles(TArray<FString>& Files, FString RootFolderFullPath, FString Ext)
{
	if(RootFolderFullPath.Len() < 1) return false;

	FPaths::NormalizeDirectoryName(RootFolderFullPath);

	IFileManager& FileManager = IFileManager::Get();

	if(!Ext.Contains(TEXT("*")))
	{
		if(Ext == "")
		{
			Ext = "*.*";
		}
		else
		{
			Ext = (Ext.Left(1) == ".") ? "*" + Ext : "*." + Ext;
		}
	}

	FString FinalPath = RootFolderFullPath + "/" + Ext;

	FileManager.FindFiles(Files, *FinalPath, true, false);
	return true;
}

#if ENGINE_MAJOR_VERSION == 4
bool UXF_BlueprintFunctionLibrary::GetStaticMeshVertexLocations(UStaticMeshComponent* Comp, int32 LodIndex, TArray<FVector>& VertexPositions)
{
	VertexPositions.Empty();

	if(!Comp)
	{
		return false;
	}

	if(!Comp->IsValidLowLevel())
	{
		return false;
	}
	//~~~~~~~~~~~~~~~~~~~~~~~

	//Component Transform
	FTransform RV_Transform = Comp->GetComponentTransform();

	//Body Setup valid?
	UBodySetup* BodySetup = Comp->GetBodySetup();

	if(!BodySetup || !BodySetup->IsValidLowLevel())
	{
		return false;
	}


	for(PxTriangleMesh* EachTriMesh : BodySetup->TriMeshes)
	{
		if (!EachTriMesh)
		{
			return false;
		}
		//~~~~~~~~~~~~~~~~

		//Number of vertices
		PxU32 VertexCount = EachTriMesh->getNbVertices();

		//Vertex array
		const PxVec3* Vertices = EachTriMesh->getVertices();

		//For each vertex, transform the position to match the component Transform
		for (PxU32 v = 0; v < VertexCount; v++)
		{
			VertexPositions.Add(RV_Transform.TransformPosition(P2UVector(Vertices[v])));
		}
	}
	return true;

	/*
	//See this wiki for more info on getting triangles
	//		https://wiki.unrealengine.com/Accessing_mesh_triangles_and_vertex_positions_in_build
	*/
}

#elif ENGINE_MAJOR_VERSION == 5
bool UXF_BlueprintFunctionLibrary::GetStaticMeshVertexLocations(UStaticMeshComponent* Comp, int32 LodIndex, TArray<FVector>& VertexPositions)
{
	if(!Comp)
	{
		return false;
	}

	TObjectPtr<UStaticMesh> MeshPtr = Comp->GetStaticMesh();
	if(!MeshPtr)
	{
		return false;
	}

	UStaticMeshDescription* Desc = MeshPtr->GetStaticMeshDescription(LodIndex);
	if(!Desc)
	{
		return false;
	}

	FTransform WorldTransform = Comp->GetComponentTransform();
	FVertexArray& Verts = Desc->Vertices();
	for (FVertexID EachVertId : Verts.GetElementIDs())
	{
		VertexPositions.Add(
			WorldTransform.TransformPosition( Desc->GetVertexPosition(EachVertId) )
		);
	}

	return true;
}
#endif


bool UXF_BlueprintFunctionLibrary::GetSkeletalMeshBoneLocations(USkeletalMeshComponent* Comp, TArray<FVector>& BoneLocations, TArray<FName>& BoneNames)
{
	if (!Comp) return false;

	BoneLocations.Empty();
	BoneNames.Empty();

	//Get Bone Names
	Comp->GetBoneNames(BoneNames);

	//Get Bone Locations
	for (int32 Itr = 0; Itr < BoneNames.Num(); Itr++ )
	{
		BoneLocations.Add(Comp->GetBoneLocation(BoneNames[Itr]));
	}

	return true;
}

#if ENGINE_MAJOR_VERSION == 4
bool UXF_BlueprintFunctionLibrary::GetSkeletalMeshVertexLocationsByLODIndex(USkeletalMeshComponent* Comp, int32 LODIndex, TArray<FVector>& VertexPositions)
{
	VertexPositions.Empty();

	if(!Comp)
	{
		return false;
	}

	if(!Comp->IsValidLowLevel())
	{
		return false;
	}

	//Component Transform
	FTransform RV_Transform = Comp->GetComponentTransform();

	int32 LODTotal = Comp->GetSkeletalMeshRenderData()->LODRenderData.Num();
	if (LODIndex > LODTotal)
	{
		UE_LOG(LogXF, Error, TEXT("LOD Error! %s only has %d LODs, but accessing %d-th LOD."), *Comp->GetOwner()->GetFName().ToString(), LODTotal, LODIndex);
		return false;
	}

	// Get Skinned Positions
	FSkeletalMeshLODRenderData& LODData = Comp->GetSkeletalMeshRenderData()->LODRenderData[LODIndex];

	TArray<FMatrix> OutRefToLocal;
	Comp->CacheRefToLocalMatrices(OutRefToLocal);

	FSkinWeightVertexBuffer& SkinWeightBuffer = *Comp->GetSkinWeightBuffer(LODIndex);

	TArray<FVector> Vertices;
	Comp->ComputeSkinnedPositions(Comp, Vertices, OutRefToLocal, LODData, SkinWeightBuffer);

	// convert each vertex to world space
	for (FVector vertex: Vertices)
	{
		VertexPositions.Add(RV_Transform.TransformPosition(vertex));
	}

	return true;

}

#elif ENGINE_MAJOR_VERSION == 5
bool UXF_BlueprintFunctionLibrary::GetSkeletalMeshVertexLocationsByLODIndex(USkeletalMeshComponent* Comp, int32 LODIndex, TArray<FVector>& VertexPositions)
{
	VertexPositions.Empty();

	if(!Comp)
	{
		return false;
	}

	if(!Comp->IsValidLowLevel())
	{
		return false;
	}

	//Component Transform
	FTransform RV_Transform = Comp->GetComponentTransform();

	int32 LODTotal = Comp->GetSkeletalMeshRenderData()->LODRenderData.Num();
	if (LODIndex > LODTotal)
	{
		UE_LOG(LogXF, Error, TEXT("LOD Error! %s only has %d LODs, but accessing %d-th LOD."), *Comp->GetOwner()->GetFName().ToString(), LODTotal, LODIndex);
		return false;
	}

	// Get Skinned Positions
	FSkeletalMeshLODRenderData& LODData = Comp->GetSkeletalMeshRenderData()->LODRenderData[LODIndex];

	TArray<FMatrix44f> OutRefToLocal;
	Comp->CacheRefToLocalMatrices(OutRefToLocal);

	FSkinWeightVertexBuffer& SkinWeightBuffer = *Comp->GetSkinWeightBuffer(LODIndex);

	TArray<FVector3f> Vertices;
	Comp->ComputeSkinnedPositions(Comp, Vertices, OutRefToLocal, LODData, SkinWeightBuffer);

	// convert each vertex to world space
	for (FVector3f vertex: Vertices)
	{
		FVector3d v;
		v.X = vertex.X;
		v.Y = vertex.Y;
		v.Z = vertex.Z;
		VertexPositions.Add(RV_Transform.TransformPosition(v));
	}

	return true;
}
#endif

bool UXF_BlueprintFunctionLibrary::GetSkeletalMeshValidFaceCentersByLODIndex(
	FRotator ActorRotator,
	FVector CameraForward,
	USkeletalMeshComponent* Comp,
	int32 LODIndex,
	TArray<FVector>& Centers
)
{
	// TODO: This is not correct.
	// The normal seems to be wrong,
	// and the vertices after choosing
	// the valid face are almost the same as the original.
	Centers.Empty();

	TArray<FVector> Vertices;
	bool isSuccess = GetSkeletalMeshVertexLocationsByLODIndex(Comp, LODIndex, Vertices);

	// check for result
	if (!isSuccess) return false;

	TArray<uint32> FaceIndices;
	FSkeletalMeshLODRenderData& LODData = Comp->GetSkeletalMeshRenderData()->LODRenderData[LODIndex];
	FMultiSizeIndexContainer& IndexContainer = LODData.MultiSizeIndexContainer;
	IndexContainer.GetIndexBuffer(FaceIndices);

	for (int i = 0; i < FaceIndices.Num() - 2; i += 3)
	{
		FVector p1 = Vertices[FaceIndices[i]];
		FVector p2 = Vertices[FaceIndices[i + 1]];
		FVector p3 = Vertices[FaceIndices[i + 2]];
		FVector center = (p1 + p2 + p3) / 3.0;

		FVector e1 = p2 - p1;
		FVector e2 = p1 - p3;

		// Convert normal from component space to world space
		FVector normal = ActorRotator.RotateVector(FVector::CrossProduct(e2, e1));

		DrawDebugLine(
			GEngine->GetWorld(),
			center,
			normal,
			FColor::Green,
			false, 0.1f, 0, 0.1f);

		float check = FVector::DotProduct(CameraForward, normal);
		if (check < 0) {
			Centers.Add(center);
		}
	}

	return true;

}


EOcclusion UXF_BlueprintFunctionLibrary::GetOcclusionFromHitResult(
	FHitResult HitResult,
	FName MeshName,
	int MeshThickness,
	bool bIsHit
)
{
	EOcclusion Occlusion = EOcclusion::NonOcclusion;
	if (bIsHit)
	{
		FName HitActorName = HitResult.GetActor()->GetFName();
		FVector HitPosition = HitResult.Location;
		FVector TraceEndPotision = HitResult.TraceEnd;
		if (HitActorName == MeshName && FVector::Dist(TraceEndPotision, HitPosition) < MeshThickness) {
			Occlusion = EOcclusion::SelfOcclusion;
		}
		// Inter-Occlusion(Green)
		if (HitActorName != MeshName) {
			Occlusion = EOcclusion::InterOcclusion;
		}
	}

	return Occlusion;
}

bool UXF_BlueprintFunctionLibrary::DetectInterOcclusionVertices(
	TArray<FVector> Vertices,
	ACameraActor* Camera,
	FName MeshName,
	TArray<EOcclusion>& VerticesOcclusion,
	float& non_occlusion_rate,
	float& self_occlusion_rate,
	float& inter_occlusion_rate,
	float MeshThickness,
	bool bDebug
)
{
	UWorld* World = Camera->GetWorld();
	FVector CameraLocation = Camera->GetActorLocation();
	EDrawDebugTrace::Type DrawDebug = EDrawDebugTrace::None;  // DrawDebugType
	if (bDebug)
		DrawDebug = EDrawDebugTrace::ForOneFrame;
	for (int i = 0; i < Vertices.Num(); i++)
	{
		FHitResult HitResult;
		FVector vertex = Vertices[i];

		bool IsHit = UKismetSystemLibrary::LineTraceSingle(
			World,
			CameraLocation,
			vertex,
			UEngineTypes::ConvertToTraceType(ECollisionChannel::ECC_Visibility),
			true,  // bTraceComplex
			TArray<AActor*>(),  // ActorsToIgnore
			DrawDebug,  // DrawDebugType
			HitResult,
			true  // bIgnoreSelf
		);

		EOcclusion Occlusion = GetOcclusionFromHitResult(HitResult, MeshName, 5, IsHit);

		VerticesOcclusion.Add(Occlusion);
	}

	// calculate occlusion rate
	int32 non_occlussion_count = 0;
	int32 self_occlusion_count = 0;
	int32 inter_occlusion_count = 0;
	for (int idx = 0; idx < VerticesOcclusion.Num(); idx++)
	{
		if (VerticesOcclusion[idx] == EOcclusion::NonOcclusion) non_occlussion_count++;
		else if (VerticesOcclusion[idx] == EOcclusion::SelfOcclusion) self_occlusion_count++;
		else if (VerticesOcclusion[idx] == EOcclusion::InterOcclusion) inter_occlusion_count++;
	}
	non_occlusion_rate = (float)non_occlussion_count / (float)VerticesOcclusion.Num();
	self_occlusion_rate = (float)self_occlusion_count / (float)VerticesOcclusion.Num();
	inter_occlusion_rate = (float)inter_occlusion_count / (float)VerticesOcclusion.Num();
	if (bDebug)
	{
		UE_LOG(LogTemp, Log, TEXT("Skeletal: %s"), *MeshName.ToString());
		UE_LOG(LogTemp, Log, TEXT("Non-occlusion rate: %f"), non_occlusion_rate);
		UE_LOG(LogTemp, Log, TEXT("Self-occlusion rate: %f"), self_occlusion_rate);
		UE_LOG(LogTemp, Log, TEXT("Inter-occlusion rate: %f"), inter_occlusion_rate);
	}

	return true;
}

bool UXF_BlueprintFunctionLibrary::DetectOcclusionMesh(
	UMeshComponent* Comp,
	ACameraActor* Camera,
	float& non_occlusion_rate,
	float& self_occlusion_rate,
	float& inter_occlusion_rate,
	int32 LODIndex,
	int32 SampleRate,
	float MeshThickness,
	bool bDebug
)
{
	FName MeshName = Comp->GetOwner()->GetFName();
	FVector MeshLocation = Comp->GetOwner()->GetActorLocation();
	FRotator MeshRotator = Comp->GetOwner()->GetActorRotation();
	if (!Comp->IsA(UStaticMeshComponent::StaticClass()) && !Comp->IsA(USkeletalMeshComponent::StaticClass()))
	{
		UE_LOG(LogXF, Error, TEXT("DetectOcclusionMesh: %s is not a valid mesh component."), *MeshName.ToString());
		return false;
	}

	FVector CameraLocation = Camera->GetActorLocation();
	FVector CameraForward = Camera->GetActorForwardVector();

	bool isSuccess = false;
	TArray<FVector> VertexPositions;
	TArray<FVector> VertexPositionsSampled;
	if (Comp->IsA(USkeletalMeshComponent::StaticClass()))
	{
		// TODO: should using valid-face-checked vertices
		isSuccess = GetSkeletalMeshVertexLocationsByLODIndex(
			Cast<USkeletalMeshComponent>(Comp),
			LODIndex,
			VertexPositions
		);
	}
	else if (Comp->IsA(UStaticMeshComponent::StaticClass()))
	{
		// TODO: should using valid-face-checked vertices
		isSuccess = GetStaticMeshVertexLocations(
			Cast<UStaticMeshComponent>(Comp),
			LODIndex,
			VertexPositions
		);
	}
	if (!isSuccess) return false;

	if (SampleRate > 1)
	{
		// sample vertex positions
		for (int idx = 0; idx < VertexPositions.Num(); idx += SampleRate)
			VertexPositionsSampled.Add(VertexPositions[idx]);
	}
	else
	{
		VertexPositionsSampled = VertexPositions;
	}

	// detect occlusion
	TArray<EOcclusion> VerticesOcclusion;
	isSuccess = DetectInterOcclusionVertices(
		VertexPositionsSampled,
		Camera,
		MeshName,
		VerticesOcclusion,
		non_occlusion_rate,
		self_occlusion_rate,
		inter_occlusion_rate,
		MeshThickness,
		bDebug
	);
	if (!isSuccess) return false;
	return true;
}


bool UXF_BlueprintFunctionLibrary::DetectInterOcclusionSkeleton(
	USkeletalMeshComponent* Comp,
	ACameraActor* Camera,
	float& non_occlusion_rate,
	float& self_occlusion_rate,
	float& inter_occlusion_rate,
	TArray<FVector>& SkeletonPositions,
	TArray<FName>& SkeletonNames,
	TArray<EOcclusion>& SkeletonOcclusion,
	float MeshThickness,
	bool bDebug
)
{
	FName MeshName = Comp->GetOwner()->GetFName();
	FVector MeshLocation = Comp->GetOwner()->GetActorLocation();
	FRotator MeshRotator = Comp->GetOwner()->GetActorRotation();

	FVector CameraLocation = Camera->GetActorLocation();
	FVector CameraForward = Camera->GetActorForwardVector();

	bool isSuccess = GetSkeletalMeshBoneLocations(
		Cast<USkeletalMeshComponent>(Comp),
		SkeletonPositions,
		SkeletonNames
	);
	if (!isSuccess) return false;

	// detect occlusion
	isSuccess = DetectInterOcclusionVertices(
		SkeletonPositions,
		Camera,
		MeshName,
		SkeletonOcclusion,
		non_occlusion_rate,
		self_occlusion_rate,
		inter_occlusion_rate,
		MeshThickness,
		bDebug
	);
	if (!isSuccess) return false;
	return true;
}


void UXF_BlueprintFunctionLibrary::MessageDialog(FText const Content)
{
	FText const title = FText::FromString("Error!");
	FMessageDialog::Open(EAppMsgType::Ok, Content, &title);
}

bool UXF_BlueprintFunctionLibrary::SetLevel(UWorld* world, ULevel* level)
{
	bool success = world->SetCurrentLevel(level);
	return success;
}


#if ENGINE_MAJOR_VERSION == 4
UPhysicsAsset* UXF_BlueprintFunctionLibrary::GeneratePhysicsAsset(USkeletalMesh* SkeletalMesh, float MinBoneSize)
{
	// get path to save the result
	FString PackageName = SkeletalMesh->GetOutermost()->GetName();
	FString ObjectName = FString::Printf(TEXT("%s_PhysicsAsset"), *SkeletalMesh->GetName());
	FString ParentPath = FString::Printf(TEXT("%s/%s"), *FPackageName::GetLongPackagePath(*PackageName), *ObjectName);

	// create asset
	UObject* Package = CreatePackage(*ParentPath);
	UObject* Object = NewObject<UPhysicsAsset>(Package, *ObjectName, RF_Public | RF_Standalone);
	FAssetRegistryModule::AssetCreated(Object);

	// physics asset settings
	UPhysicsAsset* NewPhysicsAsset = Cast<UPhysicsAsset>(Object);
	FPhysAssetCreateParams NewBodyData;
	NewBodyData.MinBoneSize = MinBoneSize;
	NewBodyData.GeomType = EFG_SingleConvexHull;
	FText CreationErrorMessage;

	//bool bSuccess = FPhysicsAssetUtils::CreateFromSkeletalMesh(NewPhysicsAsset, SkeletalMesh, NewBodyData, CreationErrorMessage, true);
	bool bSuccess = true;

	if (bSuccess) {
		RefreshSkelMeshOnPhysicsAssetChange(SkeletalMesh);
		return NewPhysicsAsset;
	}

	return nullptr;
}

#elif ENGINE_MAJOR_VERSION == 5
UPhysicsAsset* UXF_BlueprintFunctionLibrary::GeneratePhysicsAsset(USkeletalMesh* SkeletalMesh, float MinBoneSize)
{
	// get path to save the result
	FString PackageName = SkeletalMesh->GetOutermost()->GetName();
	FString ObjectName = FString::Printf(TEXT("%s_PhysicsAsset"), *SkeletalMesh->GetName());
	FString ParentPath = FString::Printf(TEXT("%s/%s"), *FPackageName::GetLongPackagePath(*PackageName), *ObjectName);

	// create asset
	UObject* Package = CreatePackage(*ParentPath);
	UObject* Object = NewObject<UPhysicsAsset>(Package, *ObjectName, RF_Public | RF_Standalone);
	FAssetRegistryModule::AssetCreated(Object);

	// physics asset settings
	UPhysicsAsset* NewPhysicsAsset = Cast<UPhysicsAsset>(Object);
	FPhysAssetCreateParams NewBodyData;
	NewBodyData.MinBoneSize = MinBoneSize;
	NewBodyData.GeomType = EFG_SingleConvexHull;
	FText CreationErrorMessage;

	bool bSuccess = FPhysicsAssetUtils::CreateFromSkeletalMesh(NewPhysicsAsset, SkeletalMesh, NewBodyData, CreationErrorMessage, true);

	if (bSuccess) {
		RefreshSkelMeshOnPhysicsAssetChange(SkeletalMesh);
		return NewPhysicsAsset;
	}

	return nullptr;
}
#endif



// Use box shape to test
void UXF_BlueprintFunctionLibrary::DivideSceneViaBoxTrace(
	const UObject* WorldContext,
	bool EnableTrace,
	int BoxHalfSize,
	FVector StartPoint,
	bool UseRandomStartPointXAndY,
	float MaxXExtend,
	float MinXExtend,
	float MaxYExtend,
	float MinYExtend,
	float HitEndZ,
	FString PathToSaveResults,
	bool VisualizeBoxes
)
{
	PathToSaveResults = PathToSaveResults.TrimStartAndEnd();
	UWorld* World = WorldContext->GetWorld();
	// Prepare ...
	GEngine->AddOnScreenDebugMessage(
		-1, 5.0, FColor::Yellow,
		FString::Printf(
			TEXT("EnableTrace: %s"),
			EnableTrace ? TEXT("true") : TEXT("false")));

	FVector StartLocation = FVector(StartPoint);
	if (UseRandomStartPointXAndY)
	{
		// Randomly pick a start location
		while (true)
		{
			const int x = round(rand() / BoxHalfSize) * BoxHalfSize;
			const int y = round(rand() / BoxHalfSize) * BoxHalfSize;
			const int z = StartPoint.Z;

			// Check if (x, y, z) in the map
			FVector Start{static_cast<float>(x), static_cast<float>(y), static_cast<float>(z)};
			FVector End = FVector(Start.X, Start.Y, HitEndZ);
			const FVector HitBoxHalfExtend = FVector(BoxHalfSize, BoxHalfSize,
			                                         BoxHalfSize);
			const FCollisionShape ColShape = FCollisionShape::MakeBox(
				HitBoxHalfExtend);
			FHitResult HitResult;
			const bool bIsHit = World->SweepSingleByChannel(
				HitResult, Start, End, FQuat::Identity, ECC_Visibility,
				ColShape);
			if (bIsHit)
			{
				StartLocation = Start;
				break;
			}
		}
	}

	// SetActorLocation(StartLocation);
	if (EnableTrace)
	{
		GEngine->AddOnScreenDebugMessage(
			-1, 15.0, FColor::Yellow,
			FString::Printf(
				TEXT("Start at: (%f, %f, %f)"),
				StartLocation.X, StartLocation.Y, StartLocation.Z));
		GEngine->AddOnScreenDebugMessage(
			-1, 15.0, FColor::Yellow,
			FString::Printf(
				TEXT("BoxHalfSize: %d"), BoxHalfSize));
	}
	else
	{
		return;
	}

	// ...
	// GEngine->AddOnScreenDebugMessage(
	// 	-1, 5.0, FColor::Yellow,
	// 	FString::Printf(
	// 		TEXT("EnalbeTrace: %s"), EnableTrace ? TEXT("true") : TEXT("false")));
	const float DeltaStep = BoxHalfSize;
	const FVector HitBoxHalfExtend = FVector(BoxHalfSize, BoxHalfSize,
	                                         BoxHalfSize);

	const FVector Origin = StartLocation;
	const auto MaxX = MaxXExtend + Origin.X;
	const auto MinX = MinXExtend + Origin.X;
	const auto MaxY = MaxYExtend + Origin.Y;
	const auto MinY = MinYExtend + Origin.Y;

	FString HitBoxesInfo = TEXT("actor_name,x,y,z,materials,visible\n");
	HitBoxesInfo += TEXT("BoxHalfSize,DeltaStep,CenterX,CenterY,CenterZ,HitEndZ\n");
	HitBoxesInfo += FString::Printf(
		TEXT("%d,%f,%f,%f,%f,%f\n"),
		BoxHalfSize, DeltaStep, Origin.X, Origin.Y, Origin.Z, HitEndZ);

	FHitResult HitResult;
	FHitResult UpHitResult;
	FHitResult VisTestHitResult;
	const FCollisionShape ColShape = FCollisionShape::MakeBox(
		HitBoxHalfExtend);
	for (auto SignX : {1, -1})
	{
		for (auto SignY : {1, -1})
		{
			int i = 0;
			int j = 0;
			int NotHitRowCount = 0;
			int NotHitCount = 0;
			while (true)
			{
				FVector Start = FVector(Origin.X + DeltaStep * i * SignX,
				                        Origin.Y + DeltaStep * j * SignY,
				                        Origin.Z);
				FVector End = FVector(Start.X, Start.Y, HitEndZ);
				const bool bIsWithinBorder = MinX < Start.X && Start.X < MaxX && MinY < Start.Y && Start.Y < MaxY;
				const bool bIsAroundOrigin = i < 10 && j < 10;

				const bool bIsHit = World->SweepSingleByChannel(
					HitResult, Start, End, FQuat::Identity, ECC_Visibility,
					ColShape);

				constexpr float Extend = 1000.f;
				const bool bIsInside = TestInside(
					WorldContext, Start, Extend, UpHitResult);

				const bool bIsVisible = TestVisible(
					WorldContext, Start, Origin, VisTestHitResult);

				if ((bIsHit || bIsInside) && bIsWithinBorder)
				{
					// Hit somewhere, and not exceed the border.
					//
					NotHitCount = 0;
					NotHitRowCount = 0;

					FHitResult& HitRes = bIsInside ? UpHitResult : HitResult;
					FVector HitLoc = HitRes.Location;
					// Save Hit info
					const FString ActorName = HitRes.GetActor()->GetName();
					// const FString MatNames = GetActorMaterialNames(
					// 	*HitRes.Actor);
					FString MatNames = TEXT("");
					HitBoxesInfo += FString::Printf(
						TEXT("%s,%f,%f,%f,%s,%d\n"),
						*ActorName,
						HitLoc.X, HitLoc.Y, HitLoc.Z - BoxHalfSize,
						*MatNames,
						bIsVisible ? 1 : 0);

					if (VisualizeBoxes)
					{
						const FVector DebugHitBoxLoc = FVector(
							HitLoc.X, HitLoc.Y,
							HitLoc.Z - HitBoxHalfExtend.Z * 2.f);
						DrawDebugBox(
							World, DebugHitBoxLoc, HitBoxHalfExtend,
							FColor::Green, true);
					}

					constexpr float DisplayTime = 2.0f;
					GEngine->AddOnScreenDebugMessage(
						-1, DisplayTime, FColor::Orange,
						FString::Printf(
							TEXT("Hit: %s At (%f, %f, %f)"),
							*HitResult.GetActor()->GetName(),
							HitLoc.X, HitLoc.Y, HitLoc.Z - BoxHalfSize));
				}
				else if (bIsAroundOrigin && bIsWithinBorder)
				{
					;	// pass
				}
				else
				{
					// Hit nowhere, maybe outside the world or the border
					//
					NotHitCount++;
					if (NotHitCount > 2)
					{
						NotHitCount = 0;
						NotHitRowCount++;
						if (NotHitRowCount > 2)
							break;
						// Next x location
						i++;
						j = 0;
						continue;
					}
				}
				// Next y location
				j++;
			}
		}
	}
	SaveTextToFile(HitBoxesInfo, PathToSaveResults);
	GEngine->AddOnScreenDebugMessage(
		-1, 100.0, FColor::Green, TEXT("Trace Done!"));
}


void UXF_BlueprintFunctionLibrary::DivideSceneViaBoxTraceBatch(
	const UObject* WorldContext,
	TArray<FVector> StartPoints,
	bool EnableTrace,
	int BoxHalfSize,
	float MaxXExtend,
	float MinXExtend,
	float MaxYExtend,
	float MinYExtend,
	float ZExtend,
	FString PathToSaveResults,
	bool VisualizeBoxes
)
{
	// Parse the save path
	FString PathToSaveStem = PathToSaveResults.TrimStartAndEnd();
	FString PathToSaveSuffix = TEXT("");
	const bool HasSuffix = PathToSaveStem.Split(
		TEXT("."),
		&PathToSaveStem,
		&PathToSaveSuffix,
		ESearchCase::IgnoreCase,
		ESearchDir::FromEnd);
	if (HasSuffix)
	{
		PathToSaveSuffix = TEXT(".") + PathToSaveSuffix;
	}
	for (int i=0; i != StartPoints.Num(); i++)
	{
		auto Point = StartPoints[i];
		const float PointHitEndZ = Point.Z - ZExtend;
		Point.Z = Point.Z + 2000.0;
		const auto PathToSave = PathToSaveStem + FString::Printf(TEXT("%03d%s"), i+1, *PathToSaveSuffix);
		DivideSceneViaBoxTrace(
			WorldContext,
			EnableTrace,
			BoxHalfSize,
			Point,
			false,
			MaxXExtend,
			MinXExtend,
			MaxYExtend,
			MinYExtend,
			PointHitEndZ,
			PathToSave,
			VisualizeBoxes
		);
	}
}


// Check if a point is inside other models
bool UXF_BlueprintFunctionLibrary::TestInside(const UObject* WorldContext, const FVector LocStart,
                                              const float Extend, FHitResult& UpHitResult)
{
	UWorld* World = WorldContext->GetWorld();
	TArray<FHitResult> UpHitResults;
	const FVector UpEnd = FVector(LocStart.X, LocStart.Y, LocStart.Z + Extend);
	const bool bIsHitUp = World->LineTraceMultiByChannel(
		UpHitResults, LocStart, UpEnd, ECC_Visibility);
	if (!bIsHitUp)
	{
		return false;
	}
	TArray<FHitResult> DownHitResults;
	const FVector DownEnd = FVector(LocStart.X, LocStart.Y, LocStart.Z - Extend);
	const bool bIsHitDown = World->LineTraceMultiByChannel(
		DownHitResults, LocStart, DownEnd, ECC_Visibility);
	if (!bIsHitDown)
	{
		return false;
	}
	// Check if hit the same actor;
	for (const auto& UpHit : UpHitResults)
	{
		for (const auto& DownHit : DownHitResults)
		{
			if (UpHit.GetActor()->GetUniqueID() == DownHit.GetActor()->GetUniqueID())
			{
				UpHitResult = UpHit;
				return true;
			}
		}
	}
	return false;
}


// Check if a point is blocked
bool UXF_BlueprintFunctionLibrary::TestVisible(const UObject* WorldContext, const FVector TestLoc,
	const FVector CamLoc, FHitResult& OutHitResult)
{
	UWorld* World = WorldContext->GetWorld();
	const bool bIsHit = World->LineTraceSingleByChannel(
		OutHitResult, TestLoc, CamLoc, ECC_Visibility);
	return !bIsHit;
}


bool UXF_BlueprintFunctionLibrary::GetCameraVisualCenterLocation(const UObject* WorldContext,
	const FVector CameraLoc, const FRotator CameraRot, FVector& CenterLoc, bool& bIsHit)
{
	UWorld* World = WorldContext->GetWorld();
	FHitResult HitRes;
	const FVector HitEnd = CameraRot.RotateVector(FVector(10000, 0, 0)) + CameraLoc;

	bIsHit = World->LineTraceSingleByChannel(
		HitRes, CameraLoc, HitEnd, ECC_Visibility);

	if (bIsHit)
	{
		CenterLoc = HitRes.Location;
	}
	else
	{
		CenterLoc = FVector(0, 0, 0);
	}
	UE_LOG(LogTemp, Warning,
		   TEXT("HitLoc: (%f, %f, %f) (%d)"),
		   CenterLoc.X, CenterLoc.Y, CenterLoc.Z, bIsHit);

	// CenterLoc = HitEnd;
	// bIsHit = true;
	// return bIsHit;
	return bIsHit;
}


void UXF_BlueprintFunctionLibrary::SaveTextToFile(const FString StringToWrite, FString PathToSave)
{
	// FString File = FPaths::ProjectConfigDir();
	// File.Append(PathToSave);
	FString File = PathToSave;

	// We will use this FileManager to deal with the file.
	IPlatformFile& FileManager = FPlatformFileManager::Get().GetPlatformFile();

	// FString StringToWrite(TEXT("Hello World. Written from Unreal Engine 4"));

	// Always first check if the file that you want to manipulate exist.
	if (!FileManager.FileExists(*File))
	{
		UE_LOG(LogTemp, Warning,
		       TEXT(
			       "FileManipulation: Warning: Can not read the file because it was not found."
		       ));
		UE_LOG(LogTemp, Warning,
		       TEXT("FileManipulation: Expected file location: %s"), *File);
	}
	// We use the LoadFileToString to load the file into
	if (FFileHelper::SaveStringToFile(StringToWrite, *File))
	{
		UE_LOG(LogTemp, Warning,
		       TEXT("FileManipulation: Sucsesfuly Written to the text file: %s"), *File);
		    //    TEXT(
			//        "FileManipulation: Sucsesfuly Written: \"%s\" to the text file"
		    //    ), *StringToWrite);
	}
	else
	{
		UE_LOG(LogTemp, Warning,
		       TEXT("FileManipulation: Failed to write FString to file."));
	}
}
