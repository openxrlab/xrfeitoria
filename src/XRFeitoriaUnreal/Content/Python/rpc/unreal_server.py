# Copyright Epic Games, Inc. All Rights Reserved.
# Ref:
# https://github.com/EpicGames/BlenderTools/blob/main/send2ue/dependencies/rpc/unreal_server.py

from . import base_server
from .base_server import BaseRPCServerManager, BaseRPCServerThread


class UnrealRPCServerThread(BaseRPCServerThread):
    def thread_safe_call(self, callable_instance, *args):
        """Implementation of a thread safe call in Unreal."""
        return lambda *args: base_server.run_in_main_thread(callable_instance, *args)


class RPCServer(BaseRPCServerManager):
    def __init__(self, port: int = 9998):
        """Initialize the unreal rpc server, with its name and specific port."""
        super(RPCServer, self).__init__()
        self.name = 'UnrealRPCServer'
        self.port = port
        self.threaded_server_class = UnrealRPCServerThread

    def start_server_thread(self):
        """Starts the server thread."""
        # TODO use a timer exposed from FTSTicker instead of slate tick, less aggressive and safer
        # https://docs.unrealengine.com/4.27/en-US/PythonAPI/class/AutomationScheduler.html?highlight=automationscheduler#unreal.AutomationScheduler
        import unreal

        unreal.register_slate_post_tick_callback(base_server.execute_queued_calls)
        super(RPCServer, self).start_server_thread()
