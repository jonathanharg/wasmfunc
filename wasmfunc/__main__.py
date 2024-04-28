import argparse
import sys

from wasmtime import Instance, Module, Store

from .file_handler import (
    compile_file,
    execute_wasm_binary_with_deno,
    generate_output_name,
)


def main():

    parser = argparse.ArgumentParser(description="A WebAssembly compiler for Python")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    compile_parser = subparsers.add_parser("compile", help="Compile a file")
    compile_parser.add_argument(
        "file", metavar="FILE", type=str, help="File to compile"
    )
    compile_parser.add_argument(
        "-gc",
        "--enable-gc",
        dest="wasmgc",
        default=False,
        action="store_true",
        help="Enable experimental garbage collection with WasmGC (default: False)",
    )
    compile_parser.add_argument(
        "-s",
        "--enable-strings",
        dest="strings",
        default=False,
        action="store_true",
        help="Enable experimental string support with WasmGC (default: False)",
    )
    compile_parser.add_argument(
        "-no",
        "--no-optimisations",
        dest="optimise",
        default=True,
        action="store_false",
        help="Disable optimizations (default: True)",
    )

    exec_parser = subparsers.add_parser("exec", help="Execute a file")
    exec_parser.add_argument("file", metavar="FILE", type=str, help="File to execute")
    exec_parser.add_argument(
        "-gc",
        "--enable-gc",
        dest="wasmgc",
        default=False,
        action="store_true",
        help="Support WasmGC in execution (default: False)",
    )
    exec_parser.add_argument("function", type=str, help="Function name to execute")
    exec_parser.add_argument("arguments", nargs="*", help="Arguments for the function")

    args = parser.parse_args()

    if args.command == "compile":
        file = args.file
        print(f"Compiling {file}...")
        compiler = compile_file(file, enable_gc=args.wasmgc, enable_str=args.strings)

        if args.optimise:
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
    elif args.command == "exec":
        if args.wasmgc:
            print(
                execute_wasm_binary_with_deno(args.file, args.function, args.arguments)
            )
        else:
            arguments = list(map(float, args.arguments))
            store = Store()
            module = Module.from_file(store.engine, args.file)
            instance = Instance(store, module, [])
            print(instance.exports(store)[args.function](store, *arguments))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
