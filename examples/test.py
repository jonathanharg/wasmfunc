import pygwasm


@pygwasm.func
def fib(n):
    """Print the Fibonacci series up to n."""
    a, b = 0, 1
    while b < n:
        print(b, end=" ")
        a, b = b, a + b

    print()


# @pygwasm.func
def hello():
    message: str
    message = "Hello world"
    print(message)


@pygwasm.func
def basic():
    a: int
    b: int
    a = 1
    b = 2
    return a + b


if __name__ == "__main__":
    # hello()
    # fib(10)
    print(basic())
