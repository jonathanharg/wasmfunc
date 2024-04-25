from typing import Callable, Sequence, TypeVar

from .file_handler import compile_file, get_wasm_runner
from .types import wasmfuncBaseType

wasmfuncType = TypeVar("wasmfuncType", bound=wasmfuncBaseType)


def wasmfunc(
    python_function: Callable[..., wasmfuncType],
    exec=False,
    enable_gc=False,
    enable_str=False,
) -> Callable[..., wasmfuncType]:  # type: ignore
    """Mark a python function as Wasm compilable. Will be executed as regular python, unless exec is set to true. To compile this function to Wasm, run `wasmfunc your_file.py`"""

    if not exec:

        def run_as_python_wrapper(*args: Sequence[wasmfuncType]) -> wasmfuncType:
            # Call the wrapped function normally
            result = python_function(*args)
            return result

        return run_as_python_wrapper

    def run_as_wasm_wrapper(*args: Sequence[wasmfuncType]) -> wasmfuncType:
        compiler = compile_file(__file__, enable_gc=enable_gc, enable_str=enable_str)
        runner = get_wasm_runner(compiler, enable_gc=enable_gc)

        result = runner(python_function.__name__, *args)
        return result

    return run_as_wasm_wrapper
