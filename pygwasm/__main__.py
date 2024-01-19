import sys
from .file_handler import compile_file, generate_output_name

for string_path in sys.argv[1:]:
    print(f"Compiling {string_path}...")
    compiler = compile_file(string_path)
    compiler.module.optimize()
    filename = generate_output_name(string_path)
    compiler.module.write_binary(filename)
