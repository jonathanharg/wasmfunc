import wasmfunc


@wasmfunc.wasmfunc()
def assignment() -> wasmfunc.i32:
    x: wasmfunc.i32 = 10
    y: wasmfunc.i32 = 15
    z = x + y
    t = x - y
    w = z * t
    return w


testinputs_assignment = [()]
