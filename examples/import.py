import wasmfunc as p

# fmt: off
from wasmfunc import wasmfunc as f, i32 as l  # isort: skip
# fmt: on


@p.wasmfunc()
def add(x: p.i32, y: l) -> p.i32:
    return x + y


@f()
def addTen(x: p.i32) -> p.i32:
    return x + 10


testinputs_add = [(4, 5), (-1, -100), (-441, 203), (0, 0), (-1, 2)]
testinputs_addTen = [(4,), (0,), (-11,), (10,), (-1,)]
