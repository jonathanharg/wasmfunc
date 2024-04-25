from wasmfunc import i32, wasmfunc


@wasmfunc()
def while_loop() -> i32:
    i: i32 = 1
    j: i32 = 0
    i += 1
    j = i
    i *= 3
    while i < 20:
        i = i + 1
        if i == 10:
            continue
        if i == 24:
            break
        j -= i
    else:
        i = i - 1
    j *= i
    return i + j


testinputs_while_loop = [()]


@wasmfunc()
def double_while() -> i32:
    i: i32 = 0
    j: i32 = 0
    while i < 20:
        i = i + 1
        while j < 50:
            j = j + 1
    return i + j


testinputs_double_while = [()]


@wasmfunc()
def if_else(x: i32) -> i32:
    a: i32 = 0
    if x > 0:
        a = 1
    else:
        a = 6
    return a


@wasmfunc()
def if_exp(x: i32) -> i32:
    # y: i32 = 1 if x > 0 else 0
    y: i32 = 1 if x > 42 else x - 5
    return y


@wasmfunc()
def while_true() -> i32:
    x = 0
    while x > 10:
        x += 1
        if x == 10:
            # return x
            break
    return x


testinputs_if_else = [(1,), (-5,), (8,)]
testinputs_if_exp = [(1,), (-5,), (8,), (55,), (545,)]
