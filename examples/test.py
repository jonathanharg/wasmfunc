from py2wasm import wasmfunc, i32

# @py2wasm.wasmfunc
# def fib(n):
#     """Print the Fibonacci series up to n."""
#     a, b = 0, 1
#     while b < n:
#         print(b, end=" ")
#         a, b = b, a + b

#     print()


# # @py2wasm.wasmfunc
# def hello():
#     message: str
#     message = "Hello world"
#     print(message)


@wasmfunc
def basic() -> i32:
    a: i32 = 2
    b: i32 = 1
    a = 1
    b = 2
    return a + b


# if __name__ == "__main__":
#     # hello()
#     # fib(10)
#     print(basic())
