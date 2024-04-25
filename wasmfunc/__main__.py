import argparse
import sys

from .file_handler import compile_file, generate_output_name


def main():

    parser = argparse.ArgumentParser(description="A WebAssembly compiler for Python")

    parser.add_argument(
        "files", metavar="FILE", type=str, nargs="+", help="Files to compile"
    )
    parser.add_argument(
        "-no",
        "--no-optimizations",
        action="store_false",
        dest="optimize",
        default=True,
        help="Disable optimizations",
    )
    parser.add_argument(
        "-gc",
        "--enable-wasmgc",
        action="store_true",
        dest="wasmgc",
        default=False,
        help="Enable garbage collection",
    )

    args = parser.parse_args()

    if len(args.files) == 0:
        parser.print_help()

    for file in args.files:
        print(f"Compiling {file}...")
        compiler = compile_file(file, enable_gc=args.wasmgc)

        if args.optimize:
            compiler.module.optimize()

        if not compiler.module.get_num_functions() > 0:
            print("No Wasm functions found")

        else:
            filename = generate_output_name(file)
            compiler.module.write_binary(filename)
            print(f"Written {filename}")
            wat_filename = generate_output_name(file, False)
            compiler.module.write_text(wat_filename)
            print(f"Written {wat_filename}")


if __name__ == "__main__":
    main()
