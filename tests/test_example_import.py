from framework import run_test_on_example

def test_add():
    run_test_on_example("import.py", "add", [(4,5), (-1,-100), (-441,203), (0,0), (-1,2)])

def test_addTen():
    run_test_on_example("import.py", "addTen", [(4,), (0,), (-11,), (10,), (-1,)])