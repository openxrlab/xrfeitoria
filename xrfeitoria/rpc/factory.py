# Ref:
# https://github.com/EpicGames/BlenderTools/blob/main/send2ue/dependencies/rpc/factory.py

import ast
import inspect
import os
import re
import sys
import textwrap
import types
from functools import wraps
from inspect import BoundArguments, signature
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple
from xmlrpc.client import Fault

from .client import RPCClient
from .validations import (
    get_line_link,
    get_source_file_path,
    validate_arguments,
    validate_file_is_saved,
    validate_key_word_parameters,
)


class RPCFactory:
    rpc_client: RPCClient = None
    file_path = None
    remap_pairs = []
    default_imports = []
    registered_function_names = []

    @classmethod
    def setup(cls, port: int, remap_pairs: List[str] = None, default_imports: List[str] = None):
        """Sets up the RPC factory.

        Args:
            port (int): The port to connect to.
            remap_pairs (List[str], optional): A list of remap pairs. Defaults to None.
            default_imports (List[str], optional): A list of default imports. Defaults to None.
        """
        if cls.rpc_client is None or cls.rpc_client.port != port:
            cls.rpc_client = RPCClient(port)
        cls.remap_pairs = remap_pairs
        cls.default_imports = default_imports or []
        if os.environ.get('RPC_RELOAD'):
            # clear the registered functions, so they can be re-registered
            cls.registered_function_names.clear()

    @staticmethod
    def _get_docstring(code: List[str], function_name: str) -> str:
        """Gets the docstring value from the functions code.

        Args:
            code (List[str]): A list of code lines.
            function_name (str): The name of the function.

        Returns:
            str: The docstring text.
        """
        # run the function code
        exec('\n'.join(code))
        # get the function from the locals
        function_instance = locals().copy().get(function_name)
        # get the doc strings from the function
        return function_instance.__doc__

    @classmethod
    def _get_callstack_references(cls, code, function):
        """Gets all references for the given code.

        Args:
            code (List[str]): A list of code lines.
            function (Callable): A callable.
        """
        import_code = cls.default_imports.copy()

        client_module = inspect.getmodule(function)
        cls.file_path = get_source_file_path(function)

        # if a list of remap pairs have been set, the file path will be remapped to the new server location
        # Note: The is useful when the server and client are not on the same machine.
        server_module_path = cls.file_path
        for client_path_root, matching_server_path_root in cls.remap_pairs or []:
            if cls.file_path.startswith(client_path_root):
                server_module_path = os.path.join(
                    matching_server_path_root,
                    cls.file_path.replace(client_path_root, '').replace(os.sep, '/').strip('/'),
                )
                break

        for key in dir(client_module):
            # skip default imports (e.g. bpy, unreal, etc)
            if key in [_key.split()[-1] for _key in cls.default_imports]:
                continue

            for line_number, line in enumerate(code):
                if line.startswith('def '):
                    continue

                # if the key is in the line, then add it to the import code
                # this re.split is used to split the line by the following characters: . ( ) [ ] =
                # e.g. ret = bpy.data.objects['Cube'] -> ["bpy", "data", "objects", "'Cube'""]
                if key in re.split('\.|\(|\)|\[|\]|\=|\ = | ', line.strip()):
                    relative_path = function.__module__.replace('.', os.path.sep)
                    import_dir = cls.file_path.strip('.py').replace(relative_path, '').strip(os.sep)
                    # add the source file to the import code
                    source_import_code = f'sys.path.append(r"{import_dir}")'
                    if source_import_code not in import_code:
                        import_code.append(source_import_code)
                    # relatively import the module from the source file
                    relative_import_code = f'from {function.__module__} import {key}'
                    if relative_import_code not in import_code:
                        import_code.append(relative_import_code)

        return textwrap.indent('\n'.join(import_code), ' ' * 4)

    @classmethod
    def _get_code(cls, function: Callable) -> List[str]:
        """Gets the code from a callable.

        Args:
            function (Callable): A callable.

        Returns:
            List[str]: A list of code lines.
        """
        import astunparse

        code = textwrap.dedent(inspect.getsource(function)).split('\n')
        code = [line for line in code if not line.strip().startswith(('@', '#'))]
        # set definition part of function into a single line
        code = astunparse.unparse(ast.parse('\n'.join(code))).split('\n')
        code = [line for line in code if line != '']  # remove empty lines

        # get the docstring from the code
        doc_string = cls._get_docstring(code, function.__name__)

        # get import code and insert them inside the function
        import_code = cls._get_callstack_references(code, function)
        code.insert(1, import_code)

        # remove the doc string
        if doc_string:
            code = '\n'.join(code).replace(doc_string, '')
            code = [line for line in code.split('\n') if not all([char == '"' or char == "'" for char in line.strip()])]

        return code

    @classmethod
    def _register(cls, function: Callable) -> List[str]:
        """Registers a given callable with the server.

        Args:
            function (Callable): A callable.

        Returns:
            List[str]: A list of code lines.
        """
        from loguru import logger

        # if function registered, skip it
        if function.__name__ in cls.registered_function_names:
            logger.debug(f'Function "{function.__name__}" has already been registered with the server!')
            return []

        code = cls._get_code(function)
        try:
            # if additional paths are explicitly set, then use them. This is useful with the client is on another
            # machine and the python paths are different
            additional_paths = list(filter(None, os.environ.get('RPC_ADDITIONAL_PYTHON_PATHS', '').split(',')))

            if not additional_paths:
                # otherwise use the current system path
                additional_paths = sys.path

            response = cls.rpc_client.proxy.add_new_callable(function.__name__, '\n'.join(code), additional_paths)
            cls.registered_function_names.append(function.__name__)
            if os.environ.get('RPC_DEBUG'):
                _code = '\n'.join(code)
                logger.debug(f'code:\n{_code}')
                logger.debug(f'response: {response}')

        except ConnectionRefusedError:
            server_name = os.environ.get(f'RPC_SERVER_{cls.rpc_client.port}', cls.rpc_client.port)
            raise ConnectionRefusedError(f'No connection could be made with "{server_name}"')

        return code

    @classmethod
    def run_function_remotely(cls, function: Callable, args: Tuple[Any]) -> Any:
        """Handles running the given function on remotely.

        Args:
            function (Callable): A callable.
            args (Tuple[Any]): A tuple of arguments.

        Returns:
            Any: The return value of the function.
        """
        validate_arguments(function, args)

        # get the remote function instance
        code = cls._register(function)
        remote_function = getattr(cls.rpc_client.proxy, function.__name__)

        current_frame = inspect.currentframe()
        outer_frame_info = inspect.getouterframes(current_frame)
        # step back 2 frames in the callstack
        caller_frame = outer_frame_info[2][0]
        # create a trace back that is relevant to the remote code rather than the code transporting it
        call_traceback = types.TracebackType(None, caller_frame, caller_frame.f_lasti, caller_frame.f_lineno)
        # call the remote function
        if not cls.rpc_client.marshall_exceptions:
            # if exceptions are not marshalled then receive the default Fault
            return remote_function(*args)

        # otherwise catch them and add a line link to them
        try:
            return remote_function(*args)
        except Exception as exception:
            stack_trace = str(exception) + get_line_link(function)
            if isinstance(exception, Fault):
                raise Fault(exception.faultCode, exception.faultString)
            raise exception.__class__(stack_trace).with_traceback(call_traceback)


def is_in_engine() -> bool:
    """Returns True if the code is running in the engine.

    Args:
        True if the code is running in the engine.
    """
    try:
        import bpy  # isort:skip

        assert bpy.context.scene.default_level_blender
        return True
    except Exception:
        pass

    # check if the code is running in unreal
    try:
        from unreal_factory import XRFeitoriaUnrealFactory  # defined in src/XRFeitoriaUnreal/Content/Python

        return True
    except Exception:
        pass

    # not running in the engine
    return False


def remote_call(
    port: int,
    default_imports: Optional[List[str]] = None,
    remap_pairs: Optional[List[Tuple]] = None,
    dec_class: bool = False,
    prefix: str = '',
    suffix: str = '',
) -> Callable:
    """A decorator that makes this function (or class) run remotely.

    Args:
        port (int): The port to connect to.
        default_imports (List[str], optional): A list of default imports. Defaults to None.
        remap_pairs (List[Tuple], optional): A list of remap pairs. Defaults to None.
        dec_class (bool, False): If True, the ``staticmethod`` with following
            prefix and suffix of class will be decorated. Defaults to False.
        prefix (str, optional): This is used when `dec_class=True`.
            Functions that start with this prefix in the class will be decorated. Defaults to ''.
        suffix (str, optional): This is used when `dec_class=True`.
            Functions that end with this suffix in the class will be decorated. Defaults to ''.

    Returns:
        Callable: A decorated function.

    Note:
        When ``dec_class=True``, only the ``staticmethod`` with ``prefix`` and ``suffix`` will be decorated.
    """

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if is_in_engine():
                return function(*args, **kwargs)

            # remove the self argument (args[0]) if it is the same as the class name
            if len(args) > 0 and args[0].__class__.__name__ == function.__qualname__.split('.')[0]:
                args = args[1:]

            # convert kwargs arguments to positional
            # https://stackoverflow.com/questions/33448997/convert-kwargs-arguments-to-positional
            func_signature = signature(function)
            bound_arguments: BoundArguments = func_signature.bind(*args, **kwargs)
            bound_arguments.apply_defaults()
            args = bound_arguments.args
            kwargs = bound_arguments.kwargs

            # convert the args
            args = list(args)  # convert tuple to list
            for index, arg in enumerate(args):
                # convert Path to string
                if isinstance(arg, Path):
                    args[index] = arg.as_posix()

            validate_file_is_saved(function)
            validate_key_word_parameters(function, kwargs)
            RPCFactory.setup(port=port, remap_pairs=remap_pairs, default_imports=default_imports)
            return RPCFactory.run_function_remotely(function, args)

        return wrapper

    if dec_class:

        def decorator_class(cls):
            for attribute, value in cls.__dict__.items():
                if (
                    isinstance(value, staticmethod)
                    and callable(getattr(cls, attribute))
                    and attribute.startswith(prefix)
                    and attribute.endswith(suffix)
                ):
                    setattr(cls, attribute, decorator(getattr(cls, attribute)))
            return cls

        return decorator_class
    else:
        return decorator
