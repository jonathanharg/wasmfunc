import os
import importlib
import importlib.util
import sys
from wasmtime import Store, Module, Instance

from pygwasm.file_handler import compile_file



def run_test_on_example(name: str, function_name:str, inputs):
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(parent, "examples", name)
    return run_test_on_file(path, function_name, inputs)



def run_test_on_file(path: str, function_name: str, inputs:list[tuple]):
    compiler = compile_file(path)

    assert compiler.module.validate()

    # Instantiate wasm runtime
    wasm_store = Store()
    wasm_module = Module(wasm_store.engine, compiler.module.emit_binary())
    wasm_instance = Instance(wasm_store, wasm_module, [])

    # Load python code from example file
    python_spec = importlib.util.spec_from_file_location("example_module", path)
    python_module = importlib.util.module_from_spec(python_spec)
    sys.modules["example_module"] = python_module
    python_spec.loader.exec_module(python_module)

    python_func = getattr(python_module, function_name)
    wasm_func = wasm_instance.exports(wasm_store)[function_name]

    for variables in inputs:
        python_output = python_func(*variables)
        wasm_output = wasm_func(wasm_store, *variables)

        assert python_output == wasm_output
