import importlib
import importlib.util
import os
import sys
from glob import glob

from wasmfunc.file_handler import compile_file, get_wasm_runner


def test_wasmfunc_file(path: str):
    enable_gc = "gc_" in path
    enable_str = "str_" in path
    compiler = compile_file(path, enable_gc=enable_gc, enable_str=enable_str)

    # Load python code from example file
    python_spec = importlib.util.spec_from_file_location("example_module", path)
    python_module = importlib.util.module_from_spec(python_spec)
    sys.modules["example_module"] = python_module
    python_spec.loader.exec_module(python_module)

    file_contents = list(filter(lambda x: not x.startswith("__"), dir(python_module)))

    testing_functions = list(
        filter(lambda x: "testinputs_" + x in file_contents, dir(python_module)),
    )

    wasm_runner = get_wasm_runner(compiler, enable_gc=enable_gc)

    for function_name in testing_functions:
        function_inputs = getattr(python_module, "testinputs_" + function_name)

        python_func = getattr(python_module, function_name)

        for variables in function_inputs:
            python_output = python_func(*variables)
            wasm_output = wasm_runner(function_name, variables)
            print(f"{python_output} == {wasm_output}")
            assert python_output == wasm_output


parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
examples_dir = os.path.join(parent_dir, "examples")


def pytest_generate_tests(metafunc):
    file_path = os.path.join(examples_dir, "*.py")
    examples = glob(file_path)
    if "path" in metafunc.fixturenames:
        metafunc.parametrize("path", examples)
