from wasmfunc import i32, wasmfunc, i64, array, f32

@wasmfunc
def create() -> i32:
    arr: array[i32] = [5, 4, 3, 2, 1]
    return arr[0]


@wasmfunc
def edit() -> i32:
    arr2: array[i32] = [5, 4, 3, 2, 1]
    arr2[1] = 0
    return arr2[1]

# @wasmfunc
# def copy() -> i32:
#     original: array[i32] = [5, 4, 3, 2, 1]
#     copy = original[:]
#     return original[0]

# @wasmfunc
# def remove() -> i32:
#     arr = [5, 4, 3, 2, 1]
#     del arr[0]
#     return arr[0]


testinputs_create = [()]
testinputs_edit = [()]
# testinputs_copy = [()]
