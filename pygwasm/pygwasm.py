#!/usr/bin/env python
from _ast import (
    Add,
    Attribute,
    BinOp,
    Call,
    Compare,
    Constant,
    FunctionDef,
    If,
    Import,
    Module,
    Name,
    Return,
    alias,
)
import ast
from typing import Any
import symtable
import binaryen


class FileVisitor(ast.NodeVisitor):
    def visit_Module(self, node: Module):
        print(f"Creating WASM Module")
        self.module = binaryen.Module()
        super().generic_visit(node)
        self.module.write_text("out")

    def visit_FunctionDef(self, node: FunctionDef):
        # TODO: This checking method is janky
        if not any([dec.value.id == "pygwasm" for dec in node.decorator_list]):
            print(f"Ignoring non WASM function {node.name}")
            return
        print(f"Creating WASM Function {node.name}")
        code = ast.unparse(node)
        stbl = symtable.symtable(code, node.name, "exec")
        print(stbl)
        print(ast.dump(node, indent=2))
        func_visitor = FunctionVisitor(self.module)
        func_visitor.visit(node)
        # return super().generic_visit(node)

    def visit_Import(self, node: Import) -> Any:
        return super().generic_visit(node)

    def visit_alias(self, node: alias) -> Any:
        return super().generic_visit(node)

    def generic_visit(self, node):
        print(
            f"Node of type {node.__class__.__name__} is not supported by pygwams. Line number {node.lineno if hasattr(node, 'lineno') else '?'}"
        )
        return super().generic_visit(node)


class FunctionVisitor(ast.NodeTransformer):
    def __init__(self, module: binaryen.Module):
        self.module = module
        self.top_level_function = True
        self.var_stack = []

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        assert self.top_level_function
        self.top_level_function = False
        name = bytes(node.name, "ascii")
        argument_types = []
        for argument in node.args.args:
            assert argument.annotation.value.id == "pygwasm"
            type_name = argument.annotation.attr
            # name = argument.arg
            type_proper = getattr(binaryen.types, type_name)
            self.var_stack.append((argument.arg, type_proper))
            argument_types.append(type_proper)
        assert node.returns.value.id == "pygwasm"
        return_type = getattr(binaryen.types, node.returns.attr)
        body = self.module.block(None, [], return_type)
        self.module.add_function(
            name, binaryen.type_create(argument_types), return_type, [], body
        )

        for body_node in node.body:
            if isinstance(body_node, ast.AST):
                expression = super().visit(body_node)
                if isinstance(expression, binaryen.expression.Expression):
                    body.append_child(expression)
                else:
                    print("Non binaryen output of node!")
        print("Done")
        self.module.add_function_export(name, name)
        self.module.optimize()
        print("Printing")
        self.module.print()
        print(f"Is valid: {self.module.validate()}")

    def visit_Name(self, node: Name) -> binaryen.Expression | None:
        # TODO: This is janky, use the built in python module
        print("Visiting Name")
        (index, var_type) = next(
            ((i, v[1]) for i, v in enumerate(self.var_stack) if v[0] == node.id),
            (None, None),
        )
        if isinstance(node.ctx, ast.Load):
            assert index is not None
            print("Replaced Name with binaryen type")
            return self.module.local_get(index, var_type)
        if isinstance(node.ctx, ast.Store):
            # if var is None:
            raise NotImplementedError
        if isinstance(node.ctx, ast.Del):
            raise NotImplementedError

    def visit_Constant(self, node: Constant) -> Any:
        if node.value is None:
            raise NotImplementedError
        if isinstance(node.value, str):
            raise NotImplementedError
        if isinstance(node.value, int):
            # TODO: Should probably bounds check this!!!
            return self.module.const(binaryen.lib.BinaryenLiteralInt32(node.value))
        if isinstance(node.value, float):
            raise NotImplementedError
        # From the docs:
        # The values represented can be simple types such as a number, string or None, but also immutable container types (tuples and frozensets) if all of their elements are constant.
        raise NotImplementedError

    def visit_Return(self, node: Return) -> Any:
        print("Visiting Return")
        value = super().visit(node.value)
        print("Replaced Return with binaryen type")
        return self.module.Return(value)

    def visit_BinOp(self, node: BinOp) -> Any:
        print("Visiting BinOp")
        left = super().visit(node.left)
        right = super().visit(node.right)
        if isinstance(node.op, ast.Add):
            if left.get_type() == right.get_type() == binaryen.i32:
                # TODO: Fix lib BinaryenAddInt32
                print("Replacing BinOp with binaryen type")
                return self.module.binary(binaryen.lib.BinaryenAddInt32(), left, right)
        elif isinstance(node.op, ast.Sub):
            if left.get_type() == right.get_type() == binaryen.i32:
                # TODO: Fix lib BinaryenAddInt32
                print("Replacing BinOp with binaryen type")
                return self.module.binary(binaryen.lib.BinaryenSubInt32(), left, right)
        else:
            raise NotImplementedError

    def visit_If(self, node: If) -> Any:
        print("Visiting If")
        condition = super().visit(node.test)
        if_true = self.module.block(None, [], binaryen.auto)
        if_false = self.module.block(None, [], binaryen.auto)

        for python_exp in node.body:
            wasm_exp = super().visit(python_exp)
            if_true.append_child(wasm_exp)

        for python_exp in node.orelse:
            wasm_exp = super().visit(python_exp)
            if_false.append_child(wasm_exp)

        return self.module.If(condition, if_true, if_false)

    def visit_Compare(self, node: Compare) -> Any:
        if len(node.comparators) > 1 or len(node.ops) > 1:
            raise NotImplementedError

        if isinstance(node.ops[0], ast.LtE):
            left = super().visit(node.left)
            right = super().visit(node.comparators[0])
            if left.get_type() == right.get_type() == binaryen.i32:
                return self.module.binary(binaryen.lib.BinaryenLeSInt32(), left, right)
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    def visit_Call(self, node: Call) -> Any:
        if len(node.keywords) > 0:
            raise NotImplementedError
        name = bytes(node.func.id, "ascii")
        args = []
        for arg in node.args:
            arg_exp = super().visit(arg)
            args.append(arg_exp)
        # TODO: Actually find out the return type dont just hard code it lol
        return self.module.call(name, args, binaryen.i32)

    def generic_visit(self, node):
        print(
            f"FUNCTION: Node of type {node.__class__.__name__} is not supported by pygwams. Line number {node.lineno if hasattr(node, 'lineno') else '?'}"
        )
        raise NotImplementedError
        # return super().generic_visit(node)
