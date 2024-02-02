def test():
    x: int = 10
    x += 1
    y = (x := 5) + 2
    a, b, c = 1, 2, 3
    x = y = z = 0
    a, (b, c), d = 1, (2, 3), 4
    y = func(x) + 10


