#!/usr/bin/env python


if __name__ == "__main__":
    import sys
    import ast

    # On MacOS
    # brew intall binaryen
    # ln -s /opt/homebrew/include/binaryen-c.h /usr/local/include/binaryen-c.h
    import binaryen

    # TODO: Handle Error cases

    for path in sys.argv[1:]:
        with open(path, "r") as file:
            print(f"Compiling {path}...")
            tree = ast.parse(file.read())
            # TODO: Module parsing
            functions: list[ast.FunctionDef] = []
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    for d in node.decorator_list:
                        # FIXME: This wont work with import aliases
                        if (
                            isinstance(d, ast.Attribute)
                            & isinstance(d.value, ast.Name)
                            & (d.value.id == "pygwasm")
                            & (d.attr == "func")
                        ):
                            functions.append(node)
            print("========= WHOLE FILE ========")
            # print(ast.dump(tree, indent=2))
            # module = binaryen.SetColorsEnabled(False)
            for func in functions:
                print(f"===== WASM Function \"{func.name}\" ======")


                print(ast.dump(func, indent=2))

else:

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
