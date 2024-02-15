import pygwasm

@pygwasm.func
def assignment() -> pygwasm.i32:
    x: pygwasm.i32 = 10
    y: pygwasm.i32 = 15
    return x + y

testinputs_assignment = [()]