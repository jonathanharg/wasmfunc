from wasmfunc import array, f32, i32, i64, wasmfunc


@wasmfunc()
def create() -> i32:
    arr: array[i32] = [5, 4, 3, 2, 1]
    return arr[0]


@wasmfunc()
def edit() -> i32:
    arr2: array[i32] = [5, 4, 3, 2, 1]
    arr2[1] = 0
    return arr2[1]


@wasmfunc()
def list_range(start: i32, stop: i32, step: i32, index: i32) -> i32:
    arr: array[i32] = list(range(start, stop, step))
    return arr[index]


@wasmfunc()
def list_lens(start: i32, stop: i32, step: i32, index: i32) -> i32:
    arr: array[i32] = list(range(start, stop, step))
    return len(arr)


# @wasmfunc()
# def copy() -> i32:
#     original: array[i32] = [5, 4, 3, 2, 1]
#     copy = original[:]
#     return original[0]

# @wasmfunc()
# def remove() -> i32:
#     arr = [5, 4, 3, 2, 1]
#     del arr[0]
#     return arr[0]

testinputs_create = [()]
testinputs_edit = [()]
testinputs_list_lens = testinputs_list_range = [
    (0, 10, 1, 3),  # Expected output: 3
    (1, 11, 2, 4),  # Expected output: 9
    (-5, 5, 3, 2),  # Expected output: 1
    (10, 20, 2, 3),  # Expected output: 14
    (5, 15, 5, 1),  # Expected output: 10
    (-10, 0, 3, 0),  # Expected output: -10
    (-5, 5, 1, 9),  # Expected output: 4
    (10, 20, 4, 2),  # Expected output: 18
    (-20, -10, 3, 2),  # Expected output: -17
]
# testinputs_copy = [()]
