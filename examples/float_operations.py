from py2wasm import f32, func


@func
def addition() -> f32:
    x: f32 = 2.0
    y: f32 = 3.0
    return x + y


# @func
# def addition_rounding() -> f64:
#     x: f64 = 0.1
#     y: f64 = 0.2
#     return x + y


@func
def subtraction() -> f32:
    x: f32 = 5.0
    y: f32 = 3.0
    return x - y


@func
def multiplication() -> f32:
    x: f32 = 5.0
    y: f32 = 3.0
    return x * y


# @func
# def division() -> f32:
#     return 6 // 2  # Integer division

# @func
# def remainder() -> f32:
#     x: f32 = 7.0
#     y: f32 = 3.0
#     return x % y  # Modulus

# @func
# def exponentiation() -> i32:
#     return 2 ** 3

# TODO: Remove the need for these for tests
testinputs_addition = [()]
testinputs_addition_rounding = [()]
testinputs_subtraction = [()]
testinputs_multiplication = [()]
testinputs_division = [()]
testinputs_remainder = [()]
