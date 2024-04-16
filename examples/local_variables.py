import py2wasm


@py2wasm.func
def assignment() -> py2wasm.i32:
    x: py2wasm.i32 = 10
    y: py2wasm.i32 = 15
    z = x + y
    t = x - y
    w = z * t
    return w


testinputs_assignment = [()]
