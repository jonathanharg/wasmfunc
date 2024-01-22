from framework import run_test_on_example


def test_addition():
    run_test_on_example("int_operations.py", "addition", [()])


def test_subtraction():
    run_test_on_example("int_operations.py", "subtraction", [()])


def test_multiplication():
    run_test_on_example("int_operations.py", "multiplication", [()])


def test_division():
    run_test_on_example("int_operations.py", "division", [()])


def test_remainder():
    run_test_on_example("int_operations.py", "remainder", [()])


# def test_exponentiation():
#     return 2 ** 3