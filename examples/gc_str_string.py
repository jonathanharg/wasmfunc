from wasmfunc import i32, string, wasmfunc


@wasmfunc()
def create() -> i32:
    arr: string = "Hello Wasm!"
    return 0


testinputs_create = [()]
