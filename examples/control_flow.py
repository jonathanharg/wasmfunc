from pygwasm import func, i32

@func
def while_loop() -> i32:
    i: i32 = 1
    j: i32 = 0
    i += 1
    j =  i
    i *= 3
    while i < 20:
        j -= i
        i = i + 1
    j *= i
    return i + j

testinputs_while_loop = [()]

@func
def double_while() -> i32:
    i: i32 = 0
    j: i32 = 0
    while i < 20:
        i = i + 1
        while j < 50:
            j = j + 1
    return i + j

testinputs_double_while = [()]

@func
def if_else(x: i32) -> i32:
    a: i32
    if x > 0:
        a = 1
    else:
        a = 6
    return a

testinputs_if_else = [(1,),(-5,),(8,)]
