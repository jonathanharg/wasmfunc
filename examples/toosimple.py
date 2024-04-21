from py2wasm import f64, wasmfunc

# TODO:
# Error if no type in func variable


@wasmfunc
def toosimple(n: f64) -> f64:
    sum: f64 = 0.0
    flip: f64 = -1.0
    i = 1
    while i < n:
        flip *= -1.0
        sum += flip / (2 * i - 1)
        i += 1
    return sum * 4.0


if __name__ == "__main__":
    print(toosimple(100_000_000))
