"""Validations for the arguments."""

from inspect import BoundArguments, signature
from typing import Any, Callable, List, Tuple, Type, Union, get_args, get_origin

__all__ = ['Validator']


class Validator:
    @classmethod
    def validate_argument_type(cls, value, typelist: List[Type]) -> None:
        """Validate the type of an argument.

        Args:
            value (Any): The value to be validated.
            typelist (List[Type]): The list of types to be validated.

        Raises:
            TypeError: If the type of the argument is not in the typelist.
        """
        if not isinstance(typelist, list):
            typelist = [typelist]
        if any([isinstance(value, tp) for tp in typelist]):
            return
        raise TypeError(
            f'Invalid argument type, expected {[tp.__name__ for tp in typelist]} (got {value.__class__.__name__} instead).'
        )

    @classmethod
    def validate_vector(cls, value, length: int):
        """Validate the type and length of a vector.

        Args:
            value (Any): The value to be validated.
            length (int): The length of the vector.

        Raises:
            TypeError: If the type of the argument is not a vector,
                or the length of the vector is not equal to the given length.
        """
        cls.validate_argument_type(value=value, typelist=[list, tuple])
        if len(value) != length:
            raise ValueError(f'Invalid vector length, expected 3 (got {len(value)} instead)')
        for val in value:
            if not isinstance(val, float) and not isinstance(val, int):
                raise TypeError(
                    f"Invalid argument type, expected 'float' vector or 'int' vector (got '{val.__class__.__name__}' in vector instead)."
                )


def get_variable_name(_type: Any) -> str:
    """Get the variable name as a string."""
    try:
        return _type.__name__
    except AttributeError:
        return str(_type)


def get_function_signature(func: Callable) -> str:
    """Get the function signature as a string."""
    _signature = signature(func)
    parameters = [f'{param.name}: {get_variable_name(param.annotation)}' for param in _signature.parameters.values()]
    return f"def {func.__name__}({', '.join(parameters)}) -> {get_variable_name(_signature.return_annotation)}:"


# TODO: finish this decorator, right now not support typing quoted as string
def validate(func: Callable) -> Callable:
    """Decorator to validate the types of arguments and return value of a function."""

    def wrapper(*args, **kwargs):
        # convert kwargs arguments to positional
        # https://stackoverflow.com/questions/33448997/convert-kwargs-arguments-to-positional
        func_signature = signature(func)
        bound_arguments: BoundArguments = func_signature.bind(*args, **kwargs)
        bound_arguments.apply_defaults()
        # Check the types of arguments before calling the decorated function
        for arg_name, arg_type in func.__annotations__.items():
            if arg_name == 'return':
                continue
            _arg = bound_arguments.arguments[arg_name]
            # List or Tuple
            if any([get_origin(arg_type) is _type for _type in [list, List, tuple, Tuple]]):
                # is list or tuple
                if not isinstance(_arg, (list, tuple)):
                    raise TypeError(
                        f'{get_function_signature(func)}\n'
                        f'    Argument "{arg_name}" must be of type "{get_variable_name(arg_type)}", '
                        f'got `{arg_name}={_arg}` (type "{get_variable_name(_arg.__class__)}") instead'
                    )
                # length for tuple
                if get_origin(arg_type) is tuple and len(_arg) != len(get_args(arg_type)):
                    raise TypeError(
                        f'{get_function_signature(func)}\n'
                        f'    Argument "{arg_name}" must be of type "{get_variable_name(arg_type)}" in length {len(get_args(arg_type))}, '
                        f'got `{arg_name}={_arg}` (length {len(_arg)}) instead'
                    )

                # type
                if not all([isinstance(_a, get_args(arg_type)) for _a in _arg]):
                    raise TypeError(
                        f'{get_function_signature(func)}\n'
                        f'    Argument "{arg_name}" must be of type "{get_variable_name(arg_type)}", '
                        f'got `{arg_name}={_arg}` (type "{get_variable_name(_arg.__class__)}") instead'
                    )

            # Union
            elif get_origin(arg_type) is Union:
                if not isinstance(_arg, get_args(arg_type)):
                    raise TypeError(
                        f'{get_function_signature(func)}\n'
                        f'    Argument "{arg_name}" must be one of type '
                        f'{[get_variable_name(_type) for _type in get_args(arg_type)]}, '
                        f'got `{arg_name}={_arg}` (type "{get_variable_name(_arg.__class__)}") instead'
                    )

            # Other types
            elif not isinstance(_arg, arg_type):
                raise TypeError(
                    f'{get_function_signature(func)}\n'
                    f'    Argument "{arg_name}" must be of type "{get_variable_name(arg_type)}", '
                    f'got `{arg_name}={_arg}` (type "{get_variable_name(_arg.__class__)}") instead'
                )

        result = func(*args, **kwargs)

        # Check the type of the return value after calling the decorated function
        return_type = func.__annotations__.get('return')
        if return_type is not None and not isinstance(result, return_type):
            raise TypeError(
                f'{get_function_signature(func)}\n'
                f'Return value must be of type "{get_variable_name(return_type)}", '
                f'got {result} (type "{get_variable_name(result.__class__)}") instead'
            )

        return result

    return wrapper
