#!/usr/bin/env python
from _ast import FunctionDef, Module
import ast
from typing import Any, TypeAlias
import symtable

i32: TypeAlias = int

class Visitor(ast.NodeVisitor):
    def visit_Module(self, node: Module):
        print(f"Creating WASM Module")
        return super().generic_visit(node)
    
    def visit_FunctionDef(self, node: FunctionDef):
        if not any([dec.value.id == 'pygwasm' for dec in node.decorator_list]):
            print(f"Ignoring non WASM function {node.name}")
            return
        print(f"Creating WASM Function {node.name}")
        return super().generic_visit(node)
    
    def generic_visit(self, node):
        print(f"Node of type {node.__class__.__name__} is not supported by pygwams. Line number {node.lineno if hasattr(node, 'lineno') else '?'}")
        return super().generic_visit(node)

if __name__ == "__main__":
    import sys

    # On MacOS
    # brew intall binaryen
    # ln -s /opt/homebrew/include/binaryen-c.h /usr/local/include/binaryen-c.h
    import binaryen

    # TODO: Handle Error cases

    for path in sys.argv[1:]:
        with open(path, "r") as file:
            print(f"Compiling {path}...")
            tree = ast.parse(file.read(), filename=path, type_comments=True)
            print(ast.dump(tree, indent=2))
            visitor = Visitor()
            visitor.visit(tree)

else:

    def func(python_function):
        def wrapper(*args, **kwargs):
            # Do something before calling the wrapped function
            print("Before calling the wrapped function")

            # Call the wrapped function
            result = python_function(*args, **kwargs)

            # Do something after calling the wrapped function
            print("After calling the wrapped function")

            return result

        return wrapper
