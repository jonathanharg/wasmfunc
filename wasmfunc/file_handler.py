import ast
import os
import subprocess
from pathlib import Path

from wasmtime import Instance, Module, Store

from .compiler import Compiler
from .pre_compiler import PreCompiler


def compile_file(input_path: str, enable_gc=False, enable_str=False):
    with open(input_path, "r", encoding="utf-8") as file:
        code = file.read()
        path = os.path.split(input_path)
        filename = path[-1]
        tree = ast.parse(code, filename=filename, type_comments=True)
        pre_compiler = PreCompiler()
        pre_compiler.visit(tree)
        compiler = Compiler(
            filename,
            pre_compiler.argument_types,
            pre_compiler.return_type,
            enable_gc=enable_gc,
            enable_str=enable_str,
        )
        compiler.visit(tree)

        compiler.module.auto_drop()
        if not compiler.module.validate():
            compiler.module.print()
            raise RuntimeError("Wasm module is not valid!")
        return compiler


def generate_output_path(input_path: str, binary=True):
    """Generates a corresponding output path for an input path. E.g. `a/b/c.py` becomes `a/b/c.wasm`.

    Args:
        input_path (str): Input file path
        binary (bool, optional): If the output is in binary format. Binary format has the extension `.wasm`, otherwise use the text format `.wat`. Defaults to True.
    """
    filename, _file_extension = os.path.splitext(input_path)

    if binary:
        return filename + ".wasm"

    return filename + ".wat"


def generate_output_name(input_path: str, binary=True):
    """Generates a corresponding output name for an input path. E.g. `a/b/c.py` becomes `c.wasm`.

    Args:
        input_path (str): Input file path
        binary (bool, optional): If the output is in binary format. Binary format has the extension `.wasm`, otherwise use the text format `.wat`. Defaults to True.
    """
    path = generate_output_path(input_path, binary)
    return os.path.split(path)[-1]


def execute_wasm_binary_with_deno(file, function, arguments):
    js_path = Path(__file__).parent.joinpath("runWasmGC.js")
    command = [
        "deno",
        "run",
        "-A",
        "--v8-flags=--experimental-wasm-stringref",
        str(js_path),
        file,
        function,
        *arguments,
    ]
    command = list(map(str, command))

    result = subprocess.run(command, stdout=subprocess.PIPE)

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Error in WasmGC runner output")

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


def get_wasm_runner(compiler: Compiler, enable_gc=False):
    if enable_gc:

        def run_wasm_gc_func(fn_name, variables_list):
            binary_name = f"./gc_runner_{compiler.filename}.wasm"
            compiler.module.write_binary(binary_name)

            value = execute_wasm_binary_with_deno(binary_name, fn_name, variables_list)
            os.remove(binary_name)

            return value

        return run_wasm_gc_func
    else:
        # Instantiate wasm runtime
        wasm_store = Store()
        wasm_module = Module(wasm_store.engine, compiler.module.emit_binary())
        wasm_instance = Instance(wasm_store, wasm_module, [])

        def run_wasm_func(wt_name, variables_list):
            wasm_func = wasm_instance.exports(wasm_store)[wt_name]
            return wasm_func(wasm_store, *variables_list)

        return run_wasm_func
