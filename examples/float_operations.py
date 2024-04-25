from wasmfunc import f32, f64, wasmfunc


@wasmfunc()
def addition() -> f32:
    x: f32 = 2.0
    y: f32 = 3.0
    return x + y


@wasmfunc()
def addition_rounding() -> f64:
    x: f64 = 0.1
    y: f64 = 0.2
    return x + y


@wasmfunc()
def subtraction() -> f32:
    x: f32 = 5.0
    y: f32 = 3.0
    return x - y


@wasmfunc()
def multiplication() -> f32:
    x: f32 = 5.0
    y: f32 = 3.0
    return x * y


@wasmfunc()
def division() -> f32:
    return 6 // 2  # Integer division


# @wasmfunc()
# def remainder() -> f32:
#     x: f32 = 7.0
#     y: f32 = 3.0
#     return x % y  # Modulus

# @func
# def exponentiation() -> i32:
#     return 2 ** 3

testinputs_addition = [()]
testinputs_addition_rounding = [()]
testinputs_subtraction = [()]
testinputs_multiplication = [()]
testinputs_division = [()]
testinputs_remainder = [()]
