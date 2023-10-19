from typing import Callable, Sequence, TypeVar
from .types import PygwasmBaseType

PygwasmType = TypeVar('PygwasmType', bound=PygwasmBaseType)


def func(python_function: Callable[..., PygwasmType]) -> Callable[..., PygwasmType]:
    """Mark a python function as WASM compilable. Will be executed as regular python, unless run with `python -m binaryen`,
    then it will be compiled to WASM.
    """
    # TODO: Improve the types on this so that function must have args, not kwargs and must be typed with binaryen types
    def wrapper(*args: Sequence[PygwasmType]) -> PygwasmType:
        # Call the wrapped function normally
        result = python_function(*args)
        return result

    return wrapper
