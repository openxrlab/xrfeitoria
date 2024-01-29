// Copyright OpenXRLab 2023-2024. All Rights Reserved.

#include "CustomMoviePipelineOutput.h"

#include "ImageWriteTask.h"
#include "ImagePixelData.h"
#include "ImageWriteQueue.h"
#include "ImageWriteStream.h"

#include "Modules/ModuleManager.h"
#include "Containers/UnrealString.h"
#include "Misc/StringFormatArg.h"
#include "Misc/FileHelper.h"
#include "Misc/FrameRate.h"
#include "Misc/Paths.h"

// #include "HAL/PlatformFilemanager.h"
// #include "HAL/PlatformTime.h"

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Animation/SkeletalMeshActor.h"

#include "MoviePipeline.h"
#include "MoviePipelineOutputSetting.h"
#include "MoviePipelineBurnInSetting.h"
#include "MoviePipelineOutputBase.h"
#include "MoviePipelineImageQuantization.h"
#include "MoviePipelineWidgetRenderSetting.h"
#include "MoviePipelineUtils.h"
#include "MovieRenderTileImage.h"
#include "MovieRenderOverlappedImage.h"
#include "MovieRenderPipelineCoreModule.h"

#include "XF_BlueprintFunctionLibrary.h"

#if ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION == 0
	#include "MoviePipelineMasterConfig.h"
#endif

DECLARE_CYCLE_STAT(TEXT("ImgSeqOutput_RecieveImageData"), STAT_ImgSeqRecieveImageData, STATGROUP_MoviePipeline);

void UCustomMoviePipelineOutput::SetupForPipelineImpl(UMoviePipeline* InPipeline)
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
		if (BoundObject->IsA(ACameraActor::StaticClass()))
		{
			ACameraActor* Camera = Cast<ACameraActor>(BoundObject);
			Cameras.Add(Camera);
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
}


void UCustomMoviePipelineOutput::OnReceiveImageDataImpl(FMoviePipelineMergerOutputFrame* InMergedOutputFrame)
{
	if (bIsFirstFrame)
	{
		// Get Output Setting
		UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelinePrimaryConfig()->FindSetting<UMoviePipelineOutputSetting>();
		// UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UMoviePipelineOutputSetting>();
		check(OutputSettings);
		int ResolutionX = OutputSettings->OutputResolution.X;
		int ResolutionY = OutputSettings->OutputResolution.Y;

		// Save Camera Transform (KRT)
		for (ACameraActor* Camera : Cameras)
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
			CamInfo.Add(ResolutionX);
			CamInfo.Add(ResolutionY);

			// Actor in level
			FString CameraNameFromLabel = Camera->GetActorNameOrLabel();
			// Actor spawned from sequence
			FString CameraNameFromName = Camera->GetFName().GetPlainNameString();
			// XXX: Hardcode way to Judge which name is correct, need to be improved
			// Should ref to
			// GetPipeline()->ResolveFilenameFormatArguments(FileNameFormatString, FormatOverrides, OutputData.FilePath, FinalFormatArgs, &Payload->SampleState.OutputState);
			// using {camera_name}

			bool bIsCameraInLevel = CameraNameFromName.StartsWith("CameraActor") || CameraNameFromName.StartsWith("CineCameraActor");
			FString CameraName = bIsCameraInLevel ? CameraNameFromLabel : CameraNameFromName;

			FString CameraTransformPath = GetOutputPath(
				DirectoryCameraInfo / CameraName,
				"dat",
				&InMergedOutputFrame->FrameOutputState
			);  // DirectoryCameraInfo/{camera_name}/{frame_idx}.dat
			CameraTransformPath = FPaths::SetExtension(
				FPaths::GetPath(CameraTransformPath),
				FPaths::GetExtension(CameraTransformPath)
			);  // get rid of the frame index
			UXF_BlueprintFunctionLibrary::SaveFloatArrayToByteFile(CamInfo, CameraTransformPath);
		}

		// Save Actor Info (stencil value)
		for (USkeletalMeshComponent* SkeletalMeshComponent : SkeletalMeshComponents)
		{
			// Actor in level
			FString MeshNameFromLabel = SkeletalMeshComponent->GetOwner()->GetActorNameOrLabel();
			// Actor spawned from sequence
			FString MeshNameFromName = SkeletalMeshComponent->GetOwner()->GetFName().GetPlainNameString();
			// Judge which name is correct
			FString MeshName = MeshNameFromName.StartsWith("SkeletalMesh") ? MeshNameFromLabel : MeshNameFromName;

			int StencilValue = SkeletalMeshComponent->CustomDepthStencilValue;

			FString ActorInfoPath = GetOutputPath(
				DirectoryActorInfo / MeshName,
				"dat",
				&InMergedOutputFrame->FrameOutputState
			);  // DirectoryActorInfo/{actor_name}/{frame_idx}.dat
			ActorInfoPath = FPaths::SetExtension(
				FPaths::GetPath(ActorInfoPath),
				FPaths::GetExtension(ActorInfoPath)
			);  // get rid of the frame index
			UXF_BlueprintFunctionLibrary::SaveFloatToByteFile(StencilValue, ActorInfoPath);
		}

		for (UStaticMeshComponent* StaticMeshComponent : StaticMeshComponents)
		{
			// Actor in level
			FString MeshNameFromLabel = StaticMeshComponent->GetOwner()->GetActorNameOrLabel();
			// Actor spawned from sequence
			FString MeshNameFromName = StaticMeshComponent->GetOwner()->GetFName().GetPlainNameString();
			// Judge which name is correct
			FString MeshName = MeshNameFromName.StartsWith("StaticMesh") ? MeshNameFromLabel : MeshNameFromName;

			int StencilValue = StaticMeshComponent->CustomDepthStencilValue;

			FString ActorInfoPath = GetOutputPath(
				DirectoryActorInfo / MeshName,
				"dat",
				&InMergedOutputFrame->FrameOutputState
			);  // DirectoryActorInfo/{actor_name}/{frame_idx}.dat
			ActorInfoPath = FPaths::SetExtension(
				FPaths::GetPath(ActorInfoPath),
				FPaths::GetExtension(ActorInfoPath)
			);  // get rid of the frame index
			UXF_BlueprintFunctionLibrary::SaveFloatToByteFile(StencilValue, ActorInfoPath);
		}

		bIsFirstFrame = false;
	}

	SCOPE_CYCLE_COUNTER(STAT_ImgSeqRecieveImageData);

	check(InMergedOutputFrame);

	// Special case for extracting Burn Ins and Widget Renderer
	TArray<MoviePipeline::FCompositePassInfo> CompositedPasses;
	MoviePipeline::GetPassCompositeData(InMergedOutputFrame, CompositedPasses);

	UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelinePrimaryConfig()->FindSetting<UMoviePipelineOutputSetting>();
	// UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UMoviePipelineOutputSetting>();
	check(OutputSettings);

	UMoviePipelineColorSetting* ColorSetting = GetPipeline()->GetPipelinePrimaryConfig()->FindSetting<UMoviePipelineColorSetting>();
	// UMoviePipelineColorSetting* ColorSetting = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UMoviePipelineColorSetting>();

	FString OutputDirectory = OutputSettings->OutputDirectory.Path;

	for (TPair<FMoviePipelinePassIdentifier, TUniquePtr<FImagePixelData>>& RenderPassData : InMergedOutputFrame->ImageOutputData)
	{
		// Don't write out a composited pass in this loop, as it will be merged with the Final Image and not written separately.
		bool bSkip = false;
		for (const MoviePipeline::FCompositePassInfo& CompositePass : CompositedPasses)
		{
			if (CompositePass.PassIdentifier == RenderPassData.Key)
			{
				bSkip = true;
				break;
			}
		}

		if (bSkip)
		{
			continue;
		}

		// Get the output file extension via the output setting
		EImageFormat PreferredOutputFormat = OutputFormat;
		FString RenderPassName;
		if (RenderPassData.Key.Name == FString("FinalImage"))
		{
			if (!bEnableRenderPass_RGB)
			{
				continue;
			}
			switch (Extension_RGB)
			{
			case ECustomImageFormat::PNG: PreferredOutputFormat = EImageFormat::PNG; break;
			case ECustomImageFormat::JPEG: PreferredOutputFormat = EImageFormat::JPEG; break;
			case ECustomImageFormat::BMP: PreferredOutputFormat = EImageFormat::BMP; break;
			case ECustomImageFormat::EXR: PreferredOutputFormat = EImageFormat::EXR; break;
			}

			if (RenderPassName_RGB.IsEmpty())
			{
				RenderPassName_RGB = FString("rgb");
			}

			RenderPassName = RenderPassName_RGB;
		}

		for (FCustomMoviePipelineRenderPass DefinedRenderPass: AdditionalRenderPasses)
		{
			if (DefinedRenderPass.SPassName == RenderPassData.Key.Name)
			{
				if (!DefinedRenderPass.bEnabled)
				{
					continue;
				}
				switch (DefinedRenderPass.Extension)
				{
				case ECustomImageFormat::PNG: PreferredOutputFormat = EImageFormat::PNG; break;
				case ECustomImageFormat::JPEG: PreferredOutputFormat = EImageFormat::JPEG; break;
				case ECustomImageFormat::BMP: PreferredOutputFormat = EImageFormat::BMP; break;
				case ECustomImageFormat::EXR: PreferredOutputFormat = EImageFormat::EXR; break;
				}

				RenderPassName = DefinedRenderPass.RenderPassName;
			}
		}

		FImagePixelDataPayload* Payload = RenderPassData.Value->GetPayload<FImagePixelDataPayload>();

		// If the output requires a transparent output (to be useful) then we'll on a per-case basis override their intended
		// filetype to something that makes that file useful.
		if (Payload->bRequireTransparentOutput)
		{
			if (PreferredOutputFormat == EImageFormat::BMP ||
				PreferredOutputFormat == EImageFormat::JPEG)
			{
				PreferredOutputFormat = EImageFormat::PNG;
			}
		}

		const TCHAR* Extension = TEXT("");
		switch (PreferredOutputFormat)
		{
		case EImageFormat::PNG: Extension = TEXT("png"); break;
		case EImageFormat::JPEG: Extension = TEXT("jpeg"); break;
		case EImageFormat::BMP: Extension = TEXT("bmp"); break;
		case EImageFormat::EXR: Extension = TEXT("exr"); break;
		}

		TUniquePtr<FImagePixelData> QuantizedPixelData = nullptr;


		switch (PreferredOutputFormat)
		{
		case EImageFormat::PNG:
		case EImageFormat::JPEG:
		case EImageFormat::BMP:
		{
			// All three of these formats only support 8 bit data, so we need to take the incoming buffer type,
			// copy it into a new 8-bit array and optionally apply a little noise to the data to help hide gradient banding.
			QuantizedPixelData = UE::MoviePipeline::QuantizeImagePixelDataToBitDepth(RenderPassData.Value.Get(), 8, nullptr, !(ColorSetting && ColorSetting->OCIOConfiguration.bIsEnabled));
			break;
		}
		case EImageFormat::EXR:
			// No quantization required, just copy the data as we will move it into the image write task.
			QuantizedPixelData = RenderPassData.Value->CopyImageData();
			break;
		default:
			check(false);
		}

		// We need to resolve the filename format string. We combine the folder and file name into one long string first
		MoviePipeline::FMoviePipelineOutputFutureData OutputData;
		OutputData.Shot = GetPipeline()->GetActiveShotList()[Payload->SampleState.OutputState.ShotIndex];
		OutputData.PassIdentifier = RenderPassData.Key;

		struct FXMLData
		{
			FString ClipName;
			FString ImageSequenceFileName;
		};

		FXMLData XMLData;
		{
			FString FileNameFormatString = OutputDirectory / OutputSettings->FileNameFormat;

			// If we're writing more than one render pass out, we need to ensure the file name has the format string in it so we don't
			// overwrite the same file multiple times. Burn In overlays don't count if they are getting composited on top of an existing file.
			const bool bIncludeRenderPass = InMergedOutputFrame->ImageOutputData.Num() - CompositedPasses.Num() > 1;
			const bool bIncludeCameraName = InMergedOutputFrame->HasDataFromMultipleCameras();
			const bool bTestFrameNumber = true;

			UE::MoviePipeline::ValidateOutputFormatString(FileNameFormatString, bIncludeRenderPass, bTestFrameNumber, bIncludeCameraName);

			// Create specific data that needs to override
			TMap<FString, FString> FormatOverrides;
			// FormatOverrides.Add(TEXT("render_pass"), RenderPassData.Key.Name);
			FormatOverrides.Add(TEXT("render_pass"), RenderPassName);
			FormatOverrides.Add(TEXT("ext"), Extension);
			FMoviePipelineFormatArgs FinalFormatArgs;
			// Resolve for XMLs
			{
				GetPipeline()->ResolveFilenameFormatArguments(/*In*/ FileNameFormatString, FormatOverrides, /*Out*/ XMLData.ImageSequenceFileName, FinalFormatArgs, &Payload->SampleState.OutputState, -Payload->SampleState.OutputState.ShotOutputFrameNumber);
			}

			// Resolve the final absolute file path to write this to
			{
				GetPipeline()->ResolveFilenameFormatArguments(FileNameFormatString, FormatOverrides, OutputData.FilePath, FinalFormatArgs, &Payload->SampleState.OutputState);

				if (FPaths::IsRelative(OutputData.FilePath))
				{
					OutputData.FilePath = FPaths::ConvertRelativePathToFull(OutputData.FilePath);
				}
			}

			// More XML resolving. Create a deterministic clipname by removing frame numbers, file extension, and any trailing .'s
			{
				UE::MoviePipeline::RemoveFrameNumberFormatStrings(FileNameFormatString, true);
				GetPipeline()->ResolveFilenameFormatArguments(FileNameFormatString, FormatOverrides, XMLData.ClipName, FinalFormatArgs, &Payload->SampleState.OutputState);
				XMLData.ClipName.RemoveFromEnd(Extension);
				XMLData.ClipName.RemoveFromEnd(".");
			}
		}

		TUniquePtr<FImageWriteTask> TileImageTask = MakeUnique<FImageWriteTask>();
		TileImageTask->Format = PreferredOutputFormat;
		TileImageTask->CompressionQuality = 100;
		TileImageTask->Filename = OutputData.FilePath;

		// We composite before flipping the alpha so that it is consistent for all formats.
		if (RenderPassData.Key == FMoviePipelinePassIdentifier(TEXT("FinalImage")))
		{
			for (const MoviePipeline::FCompositePassInfo& CompositePass : CompositedPasses)
			{
				// We don't need to copy the data here (even though it's being passed to a async system) because we already made a unique copy of the
				// burn in/widget data when we decided to composite it.
				switch (QuantizedPixelData->GetType())
				{
				case EImagePixelType::Color:
					TileImageTask->PixelPreProcessors.Add(TAsyncCompositeImage<FColor>(CompositePass.PixelData->MoveImageDataToNew()));
					break;
				case EImagePixelType::Float16:
					TileImageTask->PixelPreProcessors.Add(TAsyncCompositeImage<FFloat16Color>(CompositePass.PixelData->MoveImageDataToNew()));
					break;
				case EImagePixelType::Float32:
					TileImageTask->PixelPreProcessors.Add(TAsyncCompositeImage<FLinearColor>(CompositePass.PixelData->MoveImageDataToNew()));
					break;
				}
			}
		}


		TileImageTask->PixelData = MoveTemp(QuantizedPixelData);

#if WITH_EDITOR
		GetPipeline()->AddFrameToOutputMetadata(XMLData.ClipName, XMLData.ImageSequenceFileName, InMergedOutputFrame->FrameOutputState, Extension, Payload->bRequireTransparentOutput);
#endif

		GetPipeline()->AddOutputFuture(ImageWriteQueue->Enqueue(MoveTemp(TileImageTask)), OutputData);
	}
}

FString UCustomMoviePipelineOutput::GetOutputPath(FString PassName, FString Ext, const FMoviePipelineFrameOutputState* InOutputState)
{
	UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelinePrimaryConfig()->FindSetting<UMoviePipelineOutputSetting>();
	// UMoviePipelineOutputSetting* OutputSettings = GetPipeline()->GetPipelineMasterConfig()->FindSetting<UMoviePipelineOutputSetting>();
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
