import inspect
from typing import Callable, Sequence, TypeVar

from .file_handler import compile_file, get_wasm_runner
from .types import wasmfuncBaseType

wasmfuncType = TypeVar("wasmfuncType", bound=wasmfuncBaseType)


def wasmfunc(
    exec=False,
    enable_gc=False,
    enable_str=False,
):
    """Mark a python function as Wasm compilable. Will be executed as regular python, unless exec is set to true. To compile this function to Wasm, run `wasmfunc your_file.py`"""

    def decorator(python_function: Callable[..., wasmfuncType]):
        if not exec:

            def run_as_python_wrapper(*args: Sequence[wasmfuncType]) -> wasmfuncType:
                # Call the wrapped function normally
                result = python_function(*args)
                return result

            return run_as_python_wrapper

        def run_as_wasm_wrapper(*args: Sequence[wasmfuncType]) -> wasmfuncType:
            file_info = inspect.getframeinfo(inspect.currentframe().f_back)
            file_path = file_info.filename

            compiler = compile_file(
                file_path, enable_gc=enable_gc, enable_str=enable_str
            )
            runner = get_wasm_runner(compiler, enable_gc=enable_gc)

            result = runner(python_function.__name__, args)
            return result

        return run_as_wasm_wrapper

    return decorator
