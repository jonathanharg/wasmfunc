from pygwasm import func, i32


@func
def create() -> i32:
    arr = [5, 4, 3, 2, 1]
    return arr[1]


@func
def edit() -> i32:
    arr = [5, 4, 3, 2, 1]
    arr[1] = 0
    return arr[1]


@func
def remove() -> i32:
    arr = [5, 4, 3, 2, 1]
    del arr[0]
    return arr[0]


testinputs_create = [()]
testinputs_edit = [()]
