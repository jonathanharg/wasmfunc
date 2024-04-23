from wasmfunc import f64, wasmfunc


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


testinputs_toosimple = [(1000.0,)]
