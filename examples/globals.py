from py2wasm import func, i32

num: i32 = 6


@func
def get_global() -> i32:
    # TODO RETURN NONE
    global num
    return num


@func
def set_global(x: i32) -> i32:
    global num
    num = x
    return num
