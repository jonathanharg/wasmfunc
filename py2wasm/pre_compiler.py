#!/usr/bin/env python
from ast import Attribute, FunctionDef, Import, ImportFrom, Name, NodeVisitor, expr

import binaryen

type BinaryenType = binaryen.internals.BinaryenType
Int32 = binaryen.type.Int32
Int64 = binaryen.type.Int64
Float32 = binaryen.type.Float32
Float64 = binaryen.type.Float64


def get_binaryen_type(node: expr | None, object_aliases: dict[str, str]):
    """Convert a py2wasm annotation e.g. x:py2wasm.i32 to a binaryen type object e.g: binaryen.type.Int32()"""
    # Annotations are either Attribute(Name) e.g. py2wasm.i32
    # Or are Name e.g. by using `from py2wasm import i32`
    # Note that both the Attribute and Name can be aliased because of `import py2wasm as p`
    # Or `from py2wasm import i32 as integer32`

    if node is None:
        return None
    if not isinstance(node, (Name, Attribute)):
        raise RuntimeWarning(f"Unkown argument annotation {node} ({type(node)})")

    type_map = {"i32": Int32, "i64": Int64, "f32": Float32, "f64": Float64}

    match node:
        case Name():
            type_name = object_aliases[node.id]
            assert isinstance(type_name, str)
            return type_map[type_name]
        case Attribute():
            return type_map[node.attr]


def handle_Import(node: Import, module_aliases: list[str]):
    # Record if py2wasm is imported, or if its imported under an alias
    for module in node.names:
        if module.name == "py2wasm":
            if module.asname is not None:
                module_aliases.append(module.asname)
            else:
                module_aliases.append("py2wasm")
    return


def handle_ImportFrom(node: ImportFrom, object_aliases: dict[str, str]):
    # Record if the py2wasm decorator is imported, or if its imported under an alias
    if node.module != "py2wasm":
        return
    for function in node.names:
        if function.asname is not None:
            # Here we may have clashes. e.g. import i32 as integer and then reimports i64 as integer
            # This will cause issues, but if you're is doing this, you have bigger problems going on.
            object_aliases[function.asname] = function.name
        else:
            # Add the default name if no alias is specified
            object_aliases[function.name] = function.name
    return


class PreCompiler(NodeVisitor):
    def __init__(self) -> None:
        self.module_aliases = []
        self.object_aliases = {}

        self.argument_types: dict[str, list[BinaryenType]] = {}
        self.return_type: dict[str, BinaryenType] = {}

        super().__init__()

    def visit_FunctionDef(self, node: FunctionDef):
        """Check if function has the binaryen decorator @binaryen.func"""
        contains_wasm = False
        for decorator in node.decorator_list:
            match decorator:
                case Attribute(
                    value=Name(), attr="func"
                ) if decorator.value.id in self.module_aliases:
                    contains_wasm = True
                    break
                case Name() if self.object_aliases[decorator.id] == "func":
                    contains_wasm = True
                    break

        if not contains_wasm:
            return

        arguments = []
        for argument in node.args.args:
            arg_type = get_binaryen_type(argument.annotation, self.object_aliases)

            if arg_type is None:
                arg_type = binaryen.type.TypeNone

            arguments.append(arg_type)
        self.argument_types[node.name] = arguments

        return_type = get_binaryen_type(node.returns, self.object_aliases)

        if return_type is None:
            return_type = binaryen.type.TypeNone

        self.return_type[node.name] = return_type

    def visit_Import(self, node: Import):
        handle_Import(node, self.module_aliases)

    def visit_ImportFrom(self, node: ImportFrom):
        handle_ImportFrom(node, self.object_aliases)
