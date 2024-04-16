import importlib
import importlib.util
import os
import sys
from glob import glob

from wasmtime import Instance, Module, Store

from py2wasm.file_handler import compile_file


def test_py2wasm_file(path: str):
    # print(path)
    # assert 0 == 1
    # return
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

    file_contents = list(filter(lambda x: not x.startswith("__"), dir(python_module)))

    testing_functions = list(
        filter(lambda x: "testinputs_" + x in file_contents, dir(python_module)),
    )

    # untested_functions = list(
    #     set(file_contents)
    #     - set(testing_functions)
    #     - set(map(lambda x: "testinputs_" + x, testing_functions))
    #     - set(["py2wasm"])
    # )
    # assert len(untested_functions) == 0

    for function_name in testing_functions:
        function_inputs = getattr(python_module, "testinputs_" + function_name)

        python_func = getattr(python_module, function_name)
        wasm_func = wasm_instance.exports(wasm_store)[function_name]

        for variables in function_inputs:
            python_output = python_func(*variables)
            wasm_output = wasm_func(wasm_store, *variables)

            assert python_output == wasm_output


parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
examples_dir = os.path.join(parent_dir, "examples")


def pytest_generate_tests(metafunc):
    file_path = os.path.join(examples_dir, "*.py")
    examples = glob(file_path)
    if "path" in metafunc.fixturenames:
        metafunc.parametrize("path", examples)


# test_examples()
# run_test_on_example("fib.py", "fib", [(4,), (0,), (1,), (10,), (-1,)])
# run_test_on_example("int_operations.py", "remainder", [()])
