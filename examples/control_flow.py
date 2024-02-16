from pygwasm import func, i32

@func
def while_loop() -> i32:
    i: i32 = 1
    while i < 10:
        i = i + 1
    return i

testinputs_while = [()]

@func
def if_else(x: i32) -> i32:
    a: i32
    if x > 0:
        a = 1
    else:
        a = 6
    return a

testinputs_if_else = [(1,),(-5,),(8,)]
