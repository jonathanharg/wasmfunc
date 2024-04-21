from wasmfunc import f32, f64, i32, i64, wasmfunc


@wasmfunc
def division_i32(x: i32, y: i32) -> i32:
    return x // y


@wasmfunc
def division_i64(x: i64, y: i64) -> i64:
    return x // y


@wasmfunc
def division_f32(x: f32, y: f32) -> f32:
    return x // y


@wasmfunc
def division_f64(x: f64, y: f64) -> f64:
    return x // y


testinputs_division_i32 = testinputs_division_i64 = [
    (10, 3),
    (10, -3),
    (-10, 3),
    (-10, -3),
    (0, 3),
    (10, 1),
    (10, -1),
    (-10, 1),
    (-10, -1),
]
testinputs_division_f32 = testinputs_division_f64 = [
    (10.0, 3.0),
    (10.0, -3.0),
    (-10.0, 3.0),
    (-10.0, -3.0),
    (0.0, 3.0),
    (10.0, 1.0),
    (10.0, -1.0),
    (-10.0, 1.0),
    (-10.0, -1.0),
]
