from typing import Callable, Sequence, TypeVar

from .types import wasmfuncBaseType

wasmfuncType = TypeVar("wasmfuncType", bound=wasmfuncBaseType)


def wasmfunc(
    python_function: Callable[..., wasmfuncType]
) -> Callable[..., wasmfuncType]:
    """Mark a python function as WASM compilable. Will be executed as regular python, unless run with `python -m binaryen`,
    then it will be compiled to WASM.
    """

    def wrapper(*args: Sequence[wasmfuncType]) -> wasmfuncType:
        # Call the wrapped function normally
        result = python_function(*args)
        return result

    return wrapper
