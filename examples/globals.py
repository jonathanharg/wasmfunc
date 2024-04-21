from wasmfunc import wasmfunc, i32

num: i32 = 6


@wasmfunc
def get_global() -> i32:
    # TODO RETURN NONE
    global num
    return num


@wasmfunc
def set_global(x: i32) -> i32:
    global num
    num = x
    return num
