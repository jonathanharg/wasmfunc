#!/usr/bin/env python
from _ast import (
    AST,
    Assign,
    Attribute,
    BinOp,
    Call,
    Compare,
    Constant,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Module,
    Name,
    Return,
)
import ast
from typing import Any
import symtable
import binaryen

# NOTE: Access super() with super(type(self), self)

class Compiler(ast.NodeTransformer):
    def __init__(self, symbol_table: symtable.SymbolTable) -> None:
        # TODO: DO WE EVEN USE SYMBOL_TABLE? DO WE NEED TO PASS IT AS ARGS
        self.symbol_table = symbol_table
        self.module = binaryen.Module()
        self.module_aliases = []
        self.object_aliases = {}
        self.top_level_function = True
        self.top_level_wasm_functions = []
        self.var_stack = []
        self.debug_whole_ast = None
        super().__init__()
    
    def compile(self, node: AST) -> None:
        return self.visit(node)

    def get_binaryen_type(self, node: Attribute | Name) -> binaryen.types.BinaryenType: # type: ignore
        """Convert a pygwasm annotation e.g. x:pygwasm.i32 to a binaryen type object e.g: binaryen.i32()
        """
        # Annotations are either Attribute(Name) e.g. pygwasm.i32
        # Or are Name e.g. by using `from pygwasm import i32`
        # Note that both the Attribute and Name can be aliased because of `import pygwasm as p`
        # Or `from pygwasm import i32 as integer32`
        match node:
            case ast.Name():
                type_name = self.object_aliases[node.id]
                assert type_name is not None
                binaryen_type = getattr(binaryen, type_name)
                return binaryen_type
            case ast.Attribute(value=ast.Name()):
                assert node.value.id in self.module_aliases
                type_name = node.attr
                binaryen_type = getattr(binaryen, type_name)
                return binaryen_type

    def visit_Module(self, node: Module):
        print("Creating WASM Module")
        self.debug_whole_ast = node
        super().generic_visit(node)

    def visit_Assign(self, node: Assign) -> Any:
        if self.top_level_function:
            # Were in a top level global variable definition: ignore for now
            return

        super().generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        """ Check if function has the binaryen decorator @binaryen.func
        """
        contains_wasm = False
        for decorator in node.decorator_list:
            if isinstance(decorator, Attribute):
                assert isinstance(decorator.value, Name)
                if decorator.value.id in self.module_aliases and decorator.attr == "func":
                    contains_wasm = True
                    break
            if isinstance(decorator, Name):
                if self.object_aliases[decorator.id] == "func":
                    contains_wasm = True
                    break

        if not contains_wasm:
            print(f"Skipping non WASM Function {node.name}")
            return

        print(f"Creating WASM Function {node.name}")
        self.top_level_wasm_functions.append(node)

        # TODO: I Don't even know if we need this
        # TODO: Make sure we support/don't support inline funcitons/calling functions in functions
        assert self.top_level_function
        self.top_level_function = False

        name = bytes(node.name, "ascii")

        function_argument_types = []
        for argument in node.args.args:
            argument_type = self.get_binaryen_type(argument.annotation)
            self.var_stack.append((argument.arg, argument_type))
            function_argument_types.append(argument_type)

        return_type = self.get_binaryen_type(node.returns)

        body = self.module.block(None, [], return_type)
        self.module.add_function(
            name, binaryen.types.create(function_argument_types), return_type, [], body
        )

        for body_node in node.body:
            if isinstance(body_node, ast.AST):
                expression = super().visit(body_node)
                if isinstance(expression, binaryen.expression.Expression):
                    body.append_child(expression)
                else:
                    print("Error: Non binaryen output of node!")

        self.module.add_function_export(name, name)
        print(f"Finished compiling {node.name}, valid: {self.module.validate()}")

        # TODO: Do we need this?
        self.top_level_function = True
        self.var_stack = []

    from ._imports import visit_Import, visit_ImportFrom

    from ._variables import visit_Constant, visit_Name

    def visit_Return(self, node: Return) -> Any:
        print("-- Visiting Return")
        value = super().visit(node.value)
        return self.module.Return(value)

    def visit_BinOp(self, node: BinOp) -> Any:
        print("-- Visiting BinOp")
        left = super().visit(node.left)
        right = super().visit(node.right)
        # TODO: Temp only support i32

        if not (left.get_type() == right.get_type() == binaryen.i32):
            raise NotImplementedError

        match node.op:
            case ast.Add():
                return self.module.binary(binaryen.operations.AddInt32(), left, right)
            case ast.Sub():
                return self.module.binary(binaryen.operations.SubInt32(), left, right)
            case ast.Mult():
                return self.module.binary(binaryen.operations.MulInt32(), left, right)
            case ast.FloorDiv():
                # TODO: Assuming signed numbers, should probably bounds check this?
                return self.module.binary(binaryen.operations.DivSInt32(), left, right)
            case ast.Mod():
                return self.module.binary(binaryen.operations.RemSInt32(), left, right)
            case _:
                raise NotImplementedError

    def visit_If(self, node: If) -> Any:
        print("-- Visiting If")
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
            # TODO: Supported chained comparisons
            print("Error: Chained comparisons e.g. 1 <= a < 10 are not currently supported. Please use brackets.")
            raise NotImplementedError
        
        left = super().visit(node.left)
        right = super().visit(node.comparators[0])

        if not (left.get_type() == right.get_type() == binaryen.i32):
            raise NotImplementedError
        
        # TODO: Don't assume signed
        match node.ops[0]:
            case ast.Eq():
                return self.module.binary(binaryen.operations.EqInt32(), left, right)
            case ast.NotEq():
                return self.module.binary(binaryen.operations.NeInt32(), left, right)
            case ast.Lt():
                return self.module.binary(binaryen.operations.LtSInt32(), left, right)
            case ast.LtE():
                return self.module.binary(binaryen.operations.LeSInt32(), left, right)
            case ast.Gt():
                return self.module.binary(binaryen.operations.GtSInt32(), left, right)
            case ast.GtE():
                return self.module.binary(binaryen.operations.GeSInt32(), left, right)
            case ast.Is():
                raise NotImplementedError
            case ast.IsNot():
                raise NotImplementedError
            case ast.In():
                raise NotImplementedError
            case ast.NotIn():
                raise NotImplementedError
            case _:
                raise NotImplementedError

    def visit_Call(self, node: Call) -> Any:
        if len(node.keywords) > 0:
            print("Pygwasm does not support keyword arguments!")
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
            f"Node of type {node.__class__.__name__} is not supported by pygwasm. Line number {node.lineno if hasattr(node, 'lineno') else '?'}"
        )
        return super().generic_visit(node)
