# wasmfunc

wasmfunc is a Python to WebAssembly Compiler built for converting a typed subset of python  code to a compiled Wasm binary.

## Installation

```bash
pip install wasmfunc
```

## How to use

Annotate your python function with Wasm types

```py
# fib.py
@wasmfunc()
def fib_recursive(n: i32) -> i32:
    if n <= 1:
        return n
    else:
        return fib_recursive(n - 1) + fib_recursive(n - 2)
```

Then compile with

```bash
wasmfunc compile fib.py
# Or python -m wasmfunc compile fib.py
```

For usage of the compiler see
```bash
~ wasmfunc --help compile
usage: wasmfunc [-h] {compile,exec} ...

A WebAssembly compiler for Python

positional arguments:
  {compile,exec}  Command to execute
    compile       Compile a file
    exec          Execute a file

options:
  -h, --help      show this help message and exit
```

For specific compile and execute help do `wasmfunc compile --help` or `wasmfunc exec --help`.

For examples on how to use the WebAssembly type hinting see [examples](examples/).
