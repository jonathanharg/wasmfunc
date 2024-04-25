from wasmfunc import i32, wasmfunc


# NOTE: Works up until n = 47
@wasmfunc()
def fib_recursive(n: i32) -> i32:
    if n <= 1:
        return n
    else:
        return fib_recursive(n - 1) + fib_recursive(n - 2)


testinputs_fib_recursive = [(4,), (0,), (1,), (10,), (-1,)]


@wasmfunc()
def fib_loop(n: i32) -> i32:
    if n <= 1:
        return 0
    if n == 2:
        return 1

    previous: i32 = 0
    current: i32 = 1
    i: i32 = 2
    while i < n:
        next_fib = previous + current
        previous = current
        current = next_fib
        i += 1

    return current


testinputs_fib_loop = [(4,), (0,), (1,), (10,), (-1,)]
