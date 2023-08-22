import threading

import unreal

from .unreal_server import RPCServer


class RPC:
    rpc_server: RPCServer = None

    @classmethod
    def start(cls, block: bool = False, port: int = 9998) -> None:
        """
        Bootstraps the running unreal editor with the unreal rpc server if it doesn't already exist.
        """
        for thread in threading.enumerate():
            if thread.name == "UnrealRPCServer":
                thread.kill()

        cls.rpc_server = RPCServer(port=port)
        cls.rpc_server.start(threaded=(not block))

    @classmethod
    def shutdown(cls):
        cls.rpc_server.shutdown()
        unreal.log_warning(
            "RPC server suppose to be shutdown, but it may not be. Please consider restarting the editor."
        )


__all__ = ["RPC"]
