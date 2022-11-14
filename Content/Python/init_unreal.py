import unreal
import GLOBAL_VARS

# @unreal.uenum()
# class MyPythonEnum(unreal.EnumBase):
#     FIRST = unreal.uvalue(0)
#     SECOND = unreal.uvalue(1)
#     FOURTH = unreal.uvalue(3)

# @unreal.ustruct()
# class PythonUnrealStruct(unreal.StructBase):
#     some_string = unreal.uproperty(str)
#     some_number = unreal.uproperty(float)
#     array_of_string = unreal.uproperty(unreal.Array(str))

@unreal.ustruct()
class PathsStruct(unreal.StructBase):
    project_dirs = unreal.uproperty(str)
    feitoria_plugin_dirs = unreal.uproperty(str)
    feitoria_plugin_python_dirs = unreal.uproperty(str)

@unreal.uclass()
class XRFeitoriaBlueprintFunctionLibrary(unreal.BlueprintFunctionLibrary):

    @unreal.ufunction(static = True, params = [], ret = str, pure=True)
    def GetPluginName():
        return GLOBAL_VARS.PLUGIN_NAME
    
    @unreal.ufunction(static = True, params = [], ret = PathsStruct, pure=True)
    def GetFeitoriaPluginDirs():
        PROJECT_ROOT, PLUGIN_ROOT, PLUGIN_PYTHON_ROOT, _ = GLOBAL_VARS.get_plugin_path()
        struct = PathsStruct()
        struct.project_dirs = str(PROJECT_ROOT)
        struct.feitoria_plugin_dirs = str(PLUGIN_ROOT)
        struct.feitoria_plugin_python_dirs = str(PLUGIN_PYTHON_ROOT)
        return struct