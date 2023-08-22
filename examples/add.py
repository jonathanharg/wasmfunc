import pygwasm


@pygwasm.func
def add(x: pygwasm.i32, y: pygwasm.i32) -> pygwasm.i32:
    return x + y


@pygwasm.func
def addTen(x: pygwasm.i32) -> pygwasm.i32:
    return x + 10


@pygwasm.func
def fib(n: pygwasm.i32) -> pygwasm.i32:
    if n <= 1:
        return n
    else:
        return fib(n - 1) + fib(n - 2)


def standard(x):
    ajsldfj = 5
    print("AJLSDJFLKSJF")
    ajsldfj += 1
