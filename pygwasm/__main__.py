import sys
from .compiler import Compiler
import ast
import symtable
import os

for string_path in sys.argv[1:]:
    with open(string_path, "r", encoding="utf-8") as file:
        print(f"Compiling {string_path}...")
        code = file.read()
        path =  os.path.split(string_path)
        filename = path[-1]
        tree = ast.parse(code, filename=filename, type_comments=True)
        symbol_table = symtable.symtable(code, filename, "exec")
        compiler = Compiler(symbol_table)
        compiler.compile(tree)
        compiler.module.optimize()
        # visitor.module.write_binary(filename)
        compiler.module.print()
