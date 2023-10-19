import pygwasm as p
from pygwasm import func, i32 as l

@p.func
def add(x: p.i32, y: l) -> p.i32:
    return x + y

@func
def addTen(x: p.i32) -> p.i32:
    return x + 10
