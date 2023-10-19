import pygwasm

@pygwasm.func
def fib(n: pygwasm.i32) -> pygwasm.i32:
    if n <= 1:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
