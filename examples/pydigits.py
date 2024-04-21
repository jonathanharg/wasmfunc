# Get the nth number of Pi indexed starting at 1
# 3.13159
# 1 23456
from sys import argv
from wasmfunc import i64, wasmfunc

tmp1: i64 = 0
tmp2: i64 = 0
acc: i64 = 0
den: i64 = 1
num: i64 = 1


@wasmfunc
def extract_Digit(nth: i64) -> i64:
    global tmp1, tmp2, acc, den, num
    tmp1 = num * nth
    tmp2 = tmp1 + acc
    tmp1 = tmp2 // den

    return tmp1


@wasmfunc
def eliminate_Digit(d: i64):
    global acc, den, num
    acc = acc - den * d
    acc = acc * 10
    num = num * 10


@wasmfunc
def next_Term(k: i64):
    global acc, den, num
    k2 = k * 2 + 1
    acc = acc + num * 2
    acc = acc * k2
    den = den * k2
    num = num * k


@wasmfunc
def pidigit_main(n: i64) -> i64:
    global tmp1, tmp2, acc, den, num

    tmp1 = 0
    tmp2 = 0

    acc = 0
    den = 1
    num = 1

    i: i64 = 0
    k: i64 = 0
    while i < n:
        k += 1
        next_Term(k)

        if num > acc:
            continue

        three: i64 = 3
        four: i64 = 4
        d = extract_Digit(three)
        if d != extract_Digit(four):
            continue

        i += 1
        eliminate_Digit(d)
    return d


if __name__ == "__main__":
    print(pidigit_main(int(argv[1])))
