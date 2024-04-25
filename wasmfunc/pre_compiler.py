#!/usr/bin/env python
from ast import (
    Attribute,
    Call,
    FunctionDef,
    Import,
    ImportFrom,
    Name,
    NodeVisitor,
    Subscript,
    expr,
)

import binaryen

type BinaryenType = binaryen.internals.BinaryenType
Int32 = binaryen.type.Int32
Int64 = binaryen.type.Int64
Float32 = binaryen.type.Float32
Float64 = binaryen.type.Float64


def get_binaryen_type(node: expr | None, object_aliases: dict[str, str]):
    """Convert a wasmfunc annotation e.g. x:wasmfunc.i32 to a binaryen type object e.g: binaryen.type.Int32()"""
    # Annotations are either Attribute(Name) e.g. wasmfunc.i32
    # Or are Name e.g. by using `from wasmfunc import i32`
    # Note that both the Attribute and Name can be aliased because of `import wasmfunc as p`
    # Or `from wasmfunc import i32 as integer32`
    type_map = {"i32": Int32, "i64": Int64, "f32": Float32, "f64": Float64}

    match node:
        case None:
            return None
        case Name(id="string"):
            return binaryen.type.Stringref
        case Name():
            type_name = object_aliases[node.id]
            assert isinstance(type_name, str)
            return type_map[type_name]
        case Attribute():
            return type_map[node.attr]
        case Subscript(value=Name(id="array")):
            element_type = get_binaryen_type(node.slice, object_aliases)

            if element_type is None:
                raise RuntimeError("Cannot have a list with element type None")

            tb = binaryen.TypeBuilder(1)
            # Use not packed for now, easier I think
            tb.set_array_type(0, element_type, binaryen.type.NotPacked, True)

            return tb.build()[0]
        case _:
            raise RuntimeWarning(f"Unkown argument annotation {node} ({type(node)})")


def handle_Import(node: Import, module_aliases: list[str]):
    # Record if wasmfunc is imported, or if its imported under an alias
    for module in node.names:
        if module.name == "wasmfunc":
            if module.asname is not None:
                module_aliases.append(module.asname)
            else:
                module_aliases.append("wasmfunc")
    return


def handle_ImportFrom(node: ImportFrom, object_aliases: dict[str, str]):
    # Record if the wasmfunc decorator is imported, or if its imported under an alias
    if node.module != "wasmfunc":
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


def does_contain_wasm(
    node: FunctionDef, object_aliases: dict[str, str], module_aliases: list[str]
):
    contains_wasm = False
    for decorator in node.decorator_list:
        match decorator:
            case Call(
                func=Attribute(attr="wasmfunc", value=Name())
            ) if decorator.func.value.id in module_aliases:
                contains_wasm = True
                break
            case Call(func=Name()) if object_aliases[decorator.func.id] == "wasmfunc":
                contains_wasm = True
                break
    return contains_wasm


class PreCompiler(NodeVisitor):
    def __init__(self) -> None:
        self.module_aliases = []
        self.object_aliases = {}

        self.argument_types: dict[str, list[BinaryenType]] = {}
        self.return_type: dict[str, BinaryenType] = {}

        super().__init__()

    def visit_FunctionDef(self, node: FunctionDef):
        """Check if function has the binaryen decorator @binaryen.wasmfunc"""
        contains_wasm = does_contain_wasm(
            node, self.object_aliases, self.module_aliases
        )

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
