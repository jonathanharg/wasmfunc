import importlib
import importlib.util
import os
import subprocess
import sys
from glob import glob
import warnings

from wasmtime import Instance, Module, Store

from wasmfunc.file_handler import compile_file


def get_wasm_function(gc, compiler):
    if gc:
        # warnings.warn("Test file uses WasmGC, cannot validate output")
        def run_gc_wasm_func(fn_name, variables_list):
            command = [
                "deno",
                "run",
                "-A",
                "--v8-flags=--experimental-wasm-stringref",
                "runWasmGC.js",
                "./pytest.wasm",
                fn_name,
                *variables_list,
            ]
            command = list(map(str, command))
            print(command)

            result = subprocess.run(command, stdout=subprocess.PIPE)
            print(result.stdout)
            print(result.stderr)

            value = result.stdout.decode().strip()
            try:
                value = int(value)
            except ValueError:
                pass
            try:
                value = float(value)
            except ValueError:
                pass

            return value

        return run_gc_wasm_func
    else:
        # Instantiate wasm runtime
        wasm_store = Store()
        wasm_module = Module(wasm_store.engine, compiler.module.emit_binary())
        wasm_instance = Instance(wasm_store, wasm_module, [])

        def run_wasm_func(wt_name, variables_list):
            wasm_func = wasm_instance.exports(wasm_store)[wt_name]
            return wasm_func(wasm_store, *variables_list)

        return run_wasm_func


def test_wasmfunc_file(path: str):
    gc = "gc_" in path
    compiler = compile_file(path, wasmgc=gc)

    compiler.module.auto_drop()
    assert compiler.module.validate()

    compiler.module.write_binary("./pytest.wasm")

    # Load python code from example file
    python_spec = importlib.util.spec_from_file_location("example_module", path)
    python_module = importlib.util.module_from_spec(python_spec)
    sys.modules["example_module"] = python_module
    python_spec.loader.exec_module(python_module)

    file_contents = list(filter(lambda x: not x.startswith("__"), dir(python_module)))

    testing_functions = list(
        filter(lambda x: "testinputs_" + x in file_contents, dir(python_module)),
    )

    run_wasm_func = get_wasm_function(gc, compiler)

    for function_name in testing_functions:
        function_inputs = getattr(python_module, "testinputs_" + function_name)

        python_func = getattr(python_module, function_name)

        for variables in function_inputs:
            python_output = python_func(*variables)
            wasm_output = run_wasm_func(function_name, variables)
            print(f"{python_output} == {wasm_output}")
            assert python_output == wasm_output

    os.remove("./pytest.wasm")


parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
examples_dir = os.path.join(parent_dir, "examples")


def pytest_generate_tests(metafunc):
    file_path = os.path.join(examples_dir, "*.py")
    examples = glob(file_path)
    if "path" in metafunc.fixturenames:
        metafunc.parametrize("path", examples)
