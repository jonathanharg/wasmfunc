from framework import run_test_on_example

def test_fib():
    run_test_on_example("fib.py", "fib", [(4,), (0,), (1,), (10,), (-1,)])