from wasmfunc import f64, i32, wasmfunc


@wasmfunc()
def addition() -> i32:
    return 2 + 3


@wasmfunc()
def subtraction() -> i32:
    return 5 - 3


@wasmfunc()
def multiplication() -> i32:
    return 5 * 3


@wasmfunc()
def division() -> i32:
    return 6 // 2  # Integer division


@wasmfunc()
def remainder() -> i32:
    return 7 % 3  # Modulus


@wasmfunc()
def bidmas() -> f64:
    x: f64 = (3 + 4 * 5) * 200 // (2 * (6 - 2) + 1)
    return x


# @wasmfunc()
# def exponentiation() -> i32:
#     return 2 ** 3

testinputs_addition = [()]
testinputs_subtraction = [()]
testinputs_multiplication = [()]
testinputs_division = [()]
testinputs_remainder = [()]
testinputs_bidmas = [()]
