// Copyright Epic Games, Inc. All Rights Reserved.

#include "XRFeitoriaUnreal.h"
#include "Engine/RendererSettings.h"
#include "MovieRenderPipelineSettings.h"
#include "MoviePipelineCameraSetting.h"
#include "Settings/EditorProjectSettings.h"
#include "CustomMoviePipelineOutput.h"
#include "CustomMoviePipelineDeferredPass.h"

#define LOCTEXT_NAMESPACE "FXRFeitoriaUnrealModule"

void FXRFeitoriaUnrealModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	UE_LOG(LogTemp, Log, TEXT( "XRFeitoriaUnreal Loaded. Doing initialization." ));
	URendererSettings* Settings = GetMutableDefault<URendererSettings>();

#if ENGINE_MAJOR_VERSION == 5

	Settings->CustomDepthStencil = ECustomDepthStencil::EnabledWithStencil;
	Settings->VelocityPass = EVelocityOutputPass::BasePass;
	Settings->SaveConfig();

#elif ENGINE_MAJOR_VERSION == 4

	Settings->CustomDepthStencil = ECustomDepthStencil::EnabledWithStencil;
	Settings->bBasePassOutputsVelocity = true;
	Settings->SaveConfig();

#endif

	UMovieRenderPipelineProjectSettings* MRQ_Settings = GetMutableDefault<UMovieRenderPipelineProjectSettings>();
	MRQ_Settings->DefaultClasses.Empty();
	MRQ_Settings->DefaultClasses.Add(UCustomMoviePipelineOutput::StaticClass());
	MRQ_Settings->DefaultClasses.Add(UCustomMoviePipelineDeferredPass::StaticClass());
	MRQ_Settings->DefaultClasses.Add(UMoviePipelineCameraSetting::StaticClass());
	MRQ_Settings->SaveConfig();

	// Set Unit to Meters
	UEditorProjectAppearanceSettings* AppearanceSettings = GetMutableDefault<UEditorProjectAppearanceSettings>();
	AppearanceSettings->bDisplayUnits = true;
	AppearanceSettings->bDisplayUnitsOnComponentTransforms = true;
	AppearanceSettings->DistanceUnits.Empty();
	AppearanceSettings->DistanceUnits.Add(EUnit::Meters);
	FUnitSettings& UnitSettings = FUnitConversion::Settings();
	UnitSettings.SetDisplayUnits(EUnitType::Distance, AppearanceSettings->DistanceUnits);
	AppearanceSettings->SaveConfig();
}

void FXRFeitoriaUnrealModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FXRFeitoriaUnrealModule, XRFeitoriaUnreal)
