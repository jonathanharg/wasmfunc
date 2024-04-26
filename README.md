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

For more examples see [examples](examples/).
