if __name__ == "__main__":
    import sys
    from .pygwasm import FileVisitor
    import ast
    import symtable

    # TODO: Handle Error cases

    for path in sys.argv[1:]:
        with open(path, "r") as file:
            print(f"Compiling {path}...")
            code = file.read()
            tree = ast.parse(code, filename=path, type_comments=True)
            # print(ast.dump(tree, indent=2))
            table = symtable.symtable(code, file.name, "exec")
            print(table)
            # table.lookup("add").get_namespace()
            visitor = FileVisitor()
            visitor.visit(tree)
