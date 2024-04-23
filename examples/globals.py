from wasmfunc import i32, wasmfunc

num: i32 = 6


@wasmfunc
def get_global() -> i32:
    global num
    return num


@wasmfunc
def set_global(x: i32) -> i32:
    global num
    num += x
    return num


testinputs_get_global = [()]
testinputs_set_global = [(1,), (2,), (0,)]
