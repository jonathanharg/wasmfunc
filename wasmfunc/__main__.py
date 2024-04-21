import sys

from .file_handler import compile_file, generate_output_name

for string_path in sys.argv[1:]:
    print(f"Compiling {string_path}...")
    compiler = compile_file(string_path)
    # TODO: Flags for optimization
    compiler.module.optimize()

    if not compiler.module.get_num_functions() > 0:
        print("No Wasm functions found")

    else:
        filename = generate_output_name(string_path)
        compiler.module.write_binary(filename)
        print(f"Written {filename}")
        wat_filename = generate_output_name(string_path, False)
        compiler.module.write_text(wat_filename)
        print(f"Written {wat_filename}")
