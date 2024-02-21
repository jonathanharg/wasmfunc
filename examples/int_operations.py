from pygwasm import func, i32


@func
def addition() -> i32:
    return 2 + 3


@func
def subtraction() -> i32:
    return 5 - 3


@func
def multiplication() -> i32:
    return 5 * 3


@func
def division() -> i32:
    return 6 // 2  # Integer division


@func
def remainder() -> i32:
    return 7 % 3  # Modulus


# @func
# def exponentiation() -> i32:
#     return 2 ** 3

testinputs_addition = [()]
testinputs_subtraction = [()]
testinputs_multiplication = [()]
testinputs_division = [()]
testinputs_remainder = [()]
