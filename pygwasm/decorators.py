def func(python_function):
    def wrapper(*args, **kwargs):
        # Do something before calling the wrapped function
        print("Before calling the wrapped function")

        # Call the wrapped function
        result = python_function(*args, **kwargs)

        # Do something after calling the wrapped function
        print("After calling the wrapped function")

        return result

    return wrapper