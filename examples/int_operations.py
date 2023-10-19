import pygwasm

@pygwasm.func
def test_addition() -> pygwasm.i32:
    return 2 + 3

@pygwasm.func
def test_subtraction() -> pygwasm.i32:
    return 5 - 3

@pygwasm.func
def test_multiplication() -> pygwasm.i32:
    return 5 * 3

@pygwasm.func
def test_division() -> pygwasm.i32:
    return 6 // 2  # Integer division

@pygwasm.func
def test_remainder() -> pygwasm.i32:
    return 7 % 3  # Modulus

# @pygwasm.func
# def test_exponentiation() -> pygwasm.i32:
#     return 2 ** 3