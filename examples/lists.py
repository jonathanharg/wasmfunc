import pygwasm
from pygwasm import i32, func

@func
def create() -> i32:
    arr = [5,4,3,2,1]
    return arr[1]

@func
def edit() -> i32:
    arr = [5,4,3,2,1]
    arr[1] = 0
    return arr[1]

testinputs_create = [()]
testinputs_edit = [()]