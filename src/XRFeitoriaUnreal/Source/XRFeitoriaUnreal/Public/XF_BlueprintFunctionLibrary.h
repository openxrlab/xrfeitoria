// Copyright OpenXRLab 2023-2024. All Rights Reserved.

#pragma once

#include "Components/PostProcessComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Serialization/Archive.h"
#include "Serialization/ArchiveSaveCompressedProxy.h"
#include "Serialization/BufferArchive.h"

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "XF_BlueprintFunctionLibrary.generated.h"

DECLARE_LOG_CATEGORY_EXTERN(LogXF, Log, All);
DEFINE_LOG_CATEGORY(LogXF);

/**
 *
 */

UENUM(BlueprintType)
enum class EOcclusion : uint8
{
	NonOcclusion = 0,
	SelfOcclusion = 1,
	InterOcclusion = 2
};

UCLASS()
class XRFEITORIAUNREAL_API UXF_BlueprintFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool FileExists(FString Path);
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool SaveFloatToByteFile(float f, FString Path);
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool SaveFloatArrayToByteFile(TArray<float> FloatArray, FString Path);
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static void EmptyPostProcessMaterial(UPostProcessComponent* postprocessComponent);
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static void ModifyPostProcessMaterial(UMaterialInterface* mat, UPostProcessComponent* postprocessComponent);

	/** Saves text to filename of your choosing, make sure include whichever file extension you want in the filename, ex: SelfNotes.txt . Make sure to include the entire file path in the save directory, ex: C:\MyGameDir\BPSavedTextFiles */
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool FileIO__SaveStringTextToFile(FString SaveDirectory, FString JoyfulFileName, FString SaveText, bool AllowOverWriting = false, bool AllowAppend = false);

	UFUNCTION(BlueprintPure, Category = "XF_BPLibrary")
		static bool FileIO__GetFiles(TArray<FString>& Files, FString RootFolderFullPath, FString Ext);

	/** Takes in an Static Mesh Component and return an array of Vectors of all the vertices locations. Locations are in World Space. Returns: false if the operation could not occur. */
	UFUNCTION(BlueprintPure, Category = "XF_BPLibrary")
		static bool GetStaticMeshVertexLocations(UStaticMeshComponent* Comp, int32 LodIndex, TArray<FVector>& VertexPositions);

	/** Takes in an Skeletal Mesh Component and return an array of Vectors of all of the current bone locations and an array of corresponding bone name in each index. Locations are in World Space. Returns: false if the operation could not occur. */
	UFUNCTION(BlueprintPure, Category = "XF_BPLibrary")
		static bool GetSkeletalMeshBoneLocations(USkeletalMeshComponent* Comp, TArray<FVector>& BoneLocations, TArray<FName>& BoneNames);

	/** Takes in an Skeletal Mesh Component and return an array of Vectors of all the vertices locations. Locations are in World Space. Returns: false if the operation could not occur. */
	UFUNCTION(BlueprintPure, Category = "XF_BPLibrary")
		static bool GetSkeletalMeshVertexLocationsByLODIndex(USkeletalMeshComponent* Comp, int32 LODIndex, TArray<FVector>& VertexPositions);

	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static void MessageDialog(FText const Content);

	/** Set persistent level for world object. **/
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool SetLevel(UWorld* world, ULevel* level);

	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static UPhysicsAsset* GeneratePhysicsAsset(USkeletalMesh* SkeletalMesh, float MinBoneSize = 5.);

	/**
	Detect the occlusion of each vertex from the camera,
	and return the occlusion result in the VerticesOcclusion array.

	@param Vertices: The vertices to be detected.
	@param CameraLocation: The location of the camera.
	@param MeshName: The name of the mesh.
	@param World: The world.
	@param VerticesOcclusion: The occlusion result of each vertex.
	@param MeshThickness: The thickness of the mesh (in cm), for detecting non-occlusion.
	@param bDebug: Whether to draw debug lines.

	@return: Whether the detection is successful.
	**/
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static EOcclusion GetOcclusionFromHitResult(FHitResult HitResult, FName MeshName, int MeshThickness, bool bIsIsHit);


	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool DetectInterOcclusionVertices(
			TArray<FVector> Vertices,
			ACameraActor* Camera,
			FName MeshName,
			TArray<EOcclusion>& VerticesOcclusion,
			float& non_occlusion_rate,
			float& self_occlusion_rate,
			float& inter_occlusion_rate,
			float MeshThickness = 5.0f,
			bool bDebug = false
		);

	/** Detect Occlusion from Camera. Return: non_occlusion_rate, self_occlusion_rate, inter_occlusion_rate **/
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool DetectOcclusionMesh(
			UMeshComponent* Comp,
			ACameraActor* Camera,
			float& non_occlusion_rate,
			float& self_occlusion_rate,
			float& inter_occlusion_rate,
			int32 LODIndex = 0,
			int32 SampleRate = 1,
			float MeshThickness = 5.0f,
			bool bDebug = false
		);

	/** Detect Occlusion from Camera. Return: non_occlusion_rate, self_occlusion_rate, inter_occlusion_rate **/
	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool DetectInterOcclusionSkeleton(
			USkeletalMeshComponent* Comp,
			ACameraActor* Camera,
			float& non_occlusion_rate,
			float& self_occlusion_rate,
			float& inter_occlusion_rate,
			TArray<FVector>& SkeletonPositions,
			TArray<FName>& SkeletonNames,
			TArray<EOcclusion>& SkeletonOcclusion,
			float MeshThickness = 5.0f,
			bool bDebug = false
		);

	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary")
		static bool GetSkeletalMeshValidFaceCentersByLODIndex(
			FRotator ActorRotator,
			FVector CameraForward,
			USkeletalMeshComponent* Comp,
			int32 LODIndex,
			TArray<FVector>& Centers);


	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary",
		meta = (AdvancedDisplay = 5, WorldContext = "WorldContext"))
		static void DivideSceneViaBoxTrace(
			const UObject* WorldContext,
			bool EnableTrace = true,
			int BoxHalfSize = 20,
			FVector StartPoint = FVector(0, 0, 2000),
			bool UseRandomStartPointXAndY = false,
			float MaxXExtend = 1500,
			float MinXExtend = -1500,
			float MaxYExtend = 1500,
			float MinYExtend = -1500,
			float HitEndZ = -2000,
			FString PathToSaveResults = TEXT("../HitBoxes.txt"),
			bool VisualizeBoxes = false);

	UFUNCTION(BlueprintPure, Category = "XF_BPLibrary",
		meta = (WorldContext = "WorldContext"))
		static bool TestInside(
			const UObject* WorldContext, const FVector LocStart,
			const float Extend, FHitResult& UpHitResult);

	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary",
		meta = (WorldContext = "WorldContext"))
		static bool TestVisible(
			const UObject* WorldContext, const FVector TestLoc,
			const FVector CamLoc, FHitResult& OutHitResult);

	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary",
		meta = (AdvancedDisplay = 4, WorldContext = "WorldContext"))
		static void DivideSceneViaBoxTraceBatch(
			const UObject* WorldContext,
			TArray<FVector> StartPoints,
			bool EnableTrace = true,
			int BoxHalfSize = 20,
			float MaxXExtend = 1500,
			float MinXExtend = -1500,
			float MaxYExtend = 1500,
			float MinYExtend = -1500,
			float ZExtend = 2000,
			FString PathToSaveResults = TEXT("../HitBoxes.txt"),
			bool VisualizeBoxes = false);

	UFUNCTION(BlueprintCallable, Category = "XF_BPLibrary",
		meta = (WorldContext = "WorldContext"))
		static bool GetCameraVisualCenterLocation(
			const UObject* WorldContext,
			const FVector CameraLoc, const FRotator CameraRot,
			FVector& CenterLoc,
			bool& bIsHit);

public:
	/** Enumeration to specify any cartesian axis in positive or negative directions */
	enum class EAxis
	{
		X, Y, Z,
		Xn, Yn, Zn,
	};

	// These axes must match the order in which they are declared in EAxis
	inline static const TArray<FVector> UnitVectors =
	{
		{  1,  0,  0 }, //  X
		{  0,  1,  0 }, //  Y
		{  0,  0,  1 }, //  Z
		{ -1,  0,  0 }, // -X
		{  0, -1,  0 }, // -Y
		{  0,  0, -1 }, // -Z
	};

	static const FVector& UnitVectorFromAxisEnum(const EAxis Axis)
	{
		return UnitVectors[std::underlying_type_t<EAxis>(Axis)];
	};

	/** Converts in-place the coordinate system of the given FTransform by specifying the source axes in terms of the destination axes */
	static void ConvertCoordinateSystem(FTransform& Transform, const EAxis DstXInSrcAxis, const EAxis DstYInSrcAxis, const EAxis DstZInSrcAxis);

	/** Converts in-place an FTransform in Unreal coordinates to OpenCV coordinates */
	static void ConvertUnrealToOpenCV(FTransform& Transform);

	/** Converts in-place an FTransform in OpenCV coordinates to Unreal coordinates */
	static void ConvertOpenCVToUnreal(FTransform& Transform);

private:
	static void SaveTextToFile(
		const FString StringToWrite,
		FString PathToSave = TEXT("../HitBoxes.txt"));

};
