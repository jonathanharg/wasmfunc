import pygwasm

@pygwasm.func
def addition() -> pygwasm.i32:
    return 2 + 3

@pygwasm.func
def subtraction() -> pygwasm.i32:
    return 5 - 3

@pygwasm.func
def multiplication() -> pygwasm.i32:
    return 5 * 3

@pygwasm.func
def division() -> pygwasm.i32:
    return 6 // 2  # Integer division

@pygwasm.func
def remainder() -> pygwasm.i32:
    return 7 % 3  # Modulus

# @pygwasm.func
# def exponentiation() -> pygwasm.i32:
#     return 2 ** 3

testinputs_addition = [()]
testinputs_subtraction = [()]
testinputs_multiplication = [()]
testinputs_division = [()]
testinputs_remainder = [()]