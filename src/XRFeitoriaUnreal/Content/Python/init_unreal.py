import constants
import unreal
from rpc import RPC
from utils import Loader


@unreal.uenum()
class PythonEnumSample(unreal.EnumBase):
    FIRST = unreal.uvalue(0)
    SECOND = unreal.uvalue(1)
    FOURTH = unreal.uvalue(3)


@unreal.ustruct()
class PathsStruct(unreal.StructBase):
    project_dirs = unreal.uproperty(str)
    feitoria_plugin_dirs = unreal.uproperty(str)
    feitoria_plugin_python_dirs = unreal.uproperty(str)


@unreal.uclass()
class XRFeitoriaBlueprintFunctionLibrary(unreal.BlueprintFunctionLibrary):
    @unreal.ufunction(static=True, params=[], ret=str, pure=True)
    def GetPluginName():
        return constants.PLUGIN_NAME

    @unreal.ufunction(static=True, params=[], ret=PathsStruct, pure=True)
    def GetFeitoriaPluginDirs():
        PROJECT_ROOT, PLUGIN_ROOT, PLUGIN_PYTHON_ROOT = constants.get_plugin_path()
        struct = PathsStruct()
        struct.project_dirs = str(PROJECT_ROOT)
        struct.feitoria_plugin_dirs = str(PLUGIN_ROOT)
        struct.feitoria_plugin_python_dirs = str(PLUGIN_PYTHON_ROOT)
        return struct


def debug_init(ip: str = '127.0.0.1', port: int = 5678):
    import ptvsd

    ptvsd.enable_attach(address=(ip, port))
    unreal.log('ptvsd.enable_attach execute')


@Loader
def main(rpc_port: int = 9998):
    RPC.start(block=False, port=rpc_port)
    # debug_init()


if __name__ == '__main__':
    rpc_port = 9998

    (cmdTokens, cmdSwitches, cmdParameters) = unreal.SystemLibrary.parse_command_line(
        unreal.SystemLibrary.get_command_line()
    )
    try:
        rpc_port = int(cmdParameters['rpc_port'])
    except Exception:
        unreal.log(f'RPC port not found in command line, using default port {rpc_port}')
    main(rpc_port=rpc_port)
