from wasmfunc import wasmfunc, i32


@wasmfunc
def addition() -> i32:
    return 2 + 3


@wasmfunc
def subtraction() -> i32:
    return 5 - 3


@wasmfunc
def multiplication() -> i32:
    return 5 * 3


@wasmfunc
def division() -> i32:
    return 6 // 2  # Integer division


@wasmfunc
def remainder() -> i32:
    return 7 % 3  # Modulus


# @wasmfunc
# def exponentiation() -> i32:
#     return 2 ** 3

testinputs_addition = [()]
testinputs_subtraction = [()]
testinputs_multiplication = [()]
testinputs_division = [()]
testinputs_remainder = [()]
