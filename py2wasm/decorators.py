from typing import Callable, Sequence, TypeVar

from .types import Py2wasmBaseType

Py2wasmType = TypeVar("Py2wasmType", bound=Py2wasmBaseType)


def wasmfunc(python_function: Callable[..., Py2wasmType]) -> Callable[..., Py2wasmType]:
    """Mark a python function as WASM compilable. Will be executed as regular python, unless run with `python -m binaryen`,
    then it will be compiled to WASM.
    """

    def wrapper(*args: Sequence[Py2wasmType]) -> Py2wasmType:
        # Call the wrapped function normally
        result = python_function(*args)
        return result

    return wrapper
