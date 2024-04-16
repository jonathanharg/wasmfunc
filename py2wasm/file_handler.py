import ast
import os
import symtable

from .compiler import Compiler


def compile_file(input_path: str):
    with open(input_path, "r", encoding="utf-8") as file:
        code = file.read()
        path = os.path.split(input_path)
        filename = path[-1]
        tree = ast.parse(code, filename=filename, type_comments=True)
        symbol_table = symtable.symtable(code, filename, "exec")
        compiler = Compiler(symbol_table)
        compiler.visit(tree)
        return compiler


def generate_output_path(input_path: str, binary=True):
    """Generates a corresponding output path for an input path. E.g. `a/b/c.py` becomes `a/b/c.wasm`.

    Args:
        input_path (str): Input file path
        binary (bool, optional): If the output is in binary format. Binary format has the extension `.wasm`, otherwise use the text format `.wat`. Defaults to True.
    """
    # path =  os.path.split(input_path)
    # filename_and_extension = path[-1].split()
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