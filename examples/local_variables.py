import pygwasm


@pygwasm.func
def assignment() -> pygwasm.i32:
    x: pygwasm.i32 = 10
    y: pygwasm.i32 = 15
    z = x + y
    t = x - y
    w = z * t
    return w


testinputs_assignment = [()]
