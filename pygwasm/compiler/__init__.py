#!/usr/bin/env python
from _ast import (
    AST,
    AnnAssign,
    Assign,
    Attribute,
    BinOp,
    Call,
    Compare,
    AugAssign,
    Load,
    FunctionDef,
    If,
    Module,
    Name,
    Return,
)
import ast
import symtable
import binaryen

# NOTE: Access super() with super(type(self), self)

BinaryenType = binaryen.types.BinaryenType


class Compiler(ast.NodeTransformer):
    def __init__(self, symbol_table: symtable.SymbolTable) -> None:
        # TODO: DO WE EVEN USE SYMBOL_TABLE? DO WE NEED TO PASS IT AS ARGS
        self.symbol_table = symbol_table
        self.module = binaryen.Module()
        self.module_aliases = []
        self.object_aliases = {}
        self.in_wasm_function = False
        self.var_stack: list[tuple[str, BinaryenType]] = []
        self.while_stack = [0]
        super().__init__()

    def _create_local(self, name: str, var_type: BinaryenType) -> int:
        local_id = len(self.var_stack)
        self.var_stack.append((name, var_type))
        return local_id

    def _get_local_by_name(self, name: str):
        return next(
            ((i, var[1]) for i, var in enumerate(self.var_stack) if var[0] == name),
            None,
        )

    def compile(self, node: AST) -> None:
        return self.visit(node)

    def _get_binaryen_type(self, node: Attribute | Name) -> binaryen.types.BinaryenType:  # type: ignore
        """Convert a pygwasm annotation e.g. x:pygwasm.i32 to a binaryen type object e.g: binaryen.i32()"""
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

    def _cast_numeric_to_matching(
        self, left: binaryen.Expression, right: binaryen.Expression, lineno: int
    ):
        left_type = left.get_type()
        right_type = right.get_type()
        input_types = [left_type, right_type]

        number_types = [binaryen.i32, binaryen.i64, binaryen.f32, binaryen.f64]
        large_types = [binaryen.i64, binaryen.f64]
        float_types = [binaryen.f32, binaryen.f64]

        if any(map(lambda x: x not in number_types, input_types)):
            raise RuntimeError("Unsupported types in number operation")

        if left_type == right_type:
            return (left, right)

        print(f"Warning: performing runtime casting on line {lineno}")

        large = any(map(lambda x: x in large_types, input_types))
        floating = any(map(lambda x: x in float_types, input_types))

        if floating:
            target_type = binaryen.f64 if large else binaryen.f32
        else:
            target_type = binaryen.i64 if large else binaryen.i32

        if left_type != target_type:
            operation = self._get_numeric_conversion_op(left, target_type, lineno)
            if operation is not None:
                left = self.module.unary(operation, left)
        if right_type != target_type:
            operation = self._get_numeric_conversion_op(right, target_type, lineno)
            if operation is not None:
                right = self.module.unary(operation, right)

        return (left, right)

    def _get_numeric_conversion_op(
        self,
        target: binaryen.Expression,
        convert_to: binaryen.types.BinaryenType,
        lineno: int,
    ):
        from_type = target.get_type()
        # TODO: Support S and U ints
        # ATM Assume everything is S
        match from_type:
            case binaryen.i32:
                match convert_to:
                    case binaryen.i32:
                        return None
                    case binaryen.i64:
                        raise binaryen.operations.ExtendS32Int64()
                    case binaryen.f32:
                        return binaryen.operations.ConvertSInt32ToFloat32()
                    case binaryen.f64:
                        raise binaryen.operations.ConvertSInt32ToFloat64()
                    case _:
                        raise RuntimeError(
                            f"Can't convert from int32 to required type on line {lineno}"
                        )
            case binaryen.i64:
                match convert_to:
                    case binaryen.i32:
                        raise binaryen.operations.WrapInt64()
                    case binaryen.i64:
                        return None
                    case binaryen.f32:
                        raise binaryen.operations.ConvertSInt64ToFloat32()
                    case binaryen.f64:
                        raise binaryen.operations.ConvertSInt64ToFloat64()
                    case _:
                        raise RuntimeError(
                            f"Can't convert from int64 to required type on line {lineno}"
                        )
            case binaryen.f32:
                match convert_to:
                    case binaryen.i32:
                        raise binaryen.operations.TruncSFloat32ToInt32()
                    case binaryen.i64:
                        raise binaryen.operations.TruncSFloat32ToInt64()
                    case binaryen.f32:
                        return None
                    case binaryen.f64:
                        return binaryen.operations.PromoteFloat32()
                    case _:
                        raise RuntimeError(
                            f"Can't convert from float32 to required type on line {lineno}"
                        )
            case binaryen.f64:
                match convert_to:
                    case binaryen.i32:
                        return binaryen.operations.TruncSFloat64ToInt32()
                    case binaryen.i64:
                        return binaryen.operations.TruncSFloat64ToInt64()
                    case binaryen.f32:
                        return binaryen.operations.DemoteFloat64()
                    case binaryen.f64:
                        return None
                    case _:
                        raise RuntimeError(
                            f"Can't convert from float64 to required type on line {lineno}"
                        )
            case _:
                raise RuntimeError(
                    f"Unsupported type target in numeric conversion on line {lineno}"
                )

    def _cast_numeric_to_type(
        self,
        target: binaryen.Expression,
        convert_to: binaryen.types.BinaryenType,
        lineno: int,
    ):
        op = self._get_numeric_conversion_op(target, convert_to, lineno)
        if op is None:
            return target
        return self.module.unary(op, target)

    def visit_Module(self, node: Module):
        print("Creating WASM Module")
        super().generic_visit(node)

    def visit_Assign(self, node: Assign):
        if not self.in_wasm_function:
            # TODO: No globals atm
            return

        expressions = []
        value = self.visit(node.value)

        for target in node.targets:
            if not isinstance(target, Name):
                raise NotImplementedError

            # TODO: We assume the variable is local
            target_var = self._get_local_by_name(target.id)

            if target_var is None:
                # We are not reassigning to a variable, but creating a new one
                # Only do this if we can work out the type of the value

                if not isinstance(value, binaryen.Expression):
                    # TODO: Better error messages
                    raise RuntimeError(
                        "Initialising a variable without a type. Use x: i32 = 1 instead of x = 1."
                    )

                computed_type = value.get_type()
                new_id = self._create_local(target.id, computed_type)
                target_var = (new_id, computed_type)

            (target_index, target_type) = target_var

            assert value.get_type() == target_type
            expressions.append(self.module.local_set(target_index, value))

        if len(expressions) > 1:
            return self.module.block(None, expressions, binaryen.none)

        return expressions[0]

    def visit_AnnAssign(self, node: AnnAssign):
        if not self.in_wasm_function:
            # TODO: No globals atm
            return

        if not isinstance(node.target, Name):
            raise NotImplementedError

        if not node.simple:
            # A node is not simple if it uses tuples, attributes or subscripts
            # e.g. (a): int = 1, a.b: int, a[1]: int
            raise NotImplementedError

        name = node.target.id
        value = self.visit(node.value) if node.value is not None else None
        type_annotation = self._get_binaryen_type(node.annotation)

        # TODO: We assume the variable is local (TODO: Lookup in symtable)
        existing_variable = self._get_local_by_name(name)

        local_id = None
        if existing_variable is not None:
            (local_id, existing_type) = existing_variable

            if existing_type != type_annotation:
                # TODO: Add a work around. Delete the old variable and make a new one?
                raise RuntimeError(
                    "You cannot change the type of a variable when reassigning"
                )
            if value is None:
                raise RuntimeError(
                    "You cannot redeclare a variable in the same namespace"
                )
        else:
            local_id = self._create_local(name, type_annotation)

        if value is not None:
            cast_value = self._cast_numeric_to_type(value, type_annotation, node.lineno)
            return self.module.local_set(local_id, cast_value)

        return self.module.nop()

    def visit_AugAssign(self, node: AugAssign):
        if not isinstance(node.target, Name):
            raise NotImplementedError(
                "Probably aug-assigning with subscript or dot notation. Not currently supported."
            )
        load_target = Name(id=node.target.id, ctx=Load())
        operation = BinOp(
            left=load_target, op=node.op, right=node.value, lineno=node.lineno
        )
        hijacked_node = Assign(targets=[node.target], value=operation)
        return self.visit_Assign(hijacked_node)

    def visit_FunctionDef(self, node: FunctionDef):
        """Check if function has the binaryen decorator @binaryen.func"""
        contains_wasm = False
        for decorator in node.decorator_list:
            match decorator:
                case ast.Attribute(
                    value=ast.Name(), attr="func"
                ) if decorator.value.id in self.module_aliases:
                    contains_wasm = True
                    break
                case ast.Name() if self.object_aliases[decorator.id] == "func":
                    contains_wasm = True
                    break

        if not contains_wasm:
            print(f"Skipping non WASM Function {node.name}")
            return

        if self.in_wasm_function:
            # We are already in a WASM function, inner functions are not supported
            # TODO: support inner functions
            raise NotImplementedError

        self.in_wasm_function = True

        name = bytes(node.name, "ascii")

        if node.args.kwarg:
            raise RuntimeError("kwargs not supported")
        if any(default for default in node.args.defaults):
            raise RuntimeError("Defaults not supported")

        function_argument_types = []
        for argument in node.args.args:
            argument_type = self._get_binaryen_type(argument.annotation)
            self._create_local(argument.arg, argument_type)
            function_argument_types.append(argument_type)

        return_type = self._get_binaryen_type(node.returns)

        body = self.module.block(None, [], return_type)

        for body_node in node.body:
            if isinstance(body_node, ast.AST):
                expression = super().visit(body_node)
                if isinstance(expression, binaryen.expression.Expression):
                    body.append_child(expression)
                else:
                    print("Error: Non binaryen output of node!")

        local_variables = self.var_stack[len(node.args.args) :]
        local_variable_types = list(map(lambda x: x[1], local_variables))

        function_ref = self.module.add_function(
            name,
            binaryen.types.create(function_argument_types),
            return_type,
            local_variable_types,
            body,
        )
        self.module.auto_drop()
        self.module.add_function_export(name, name)
        print(f"Finished compiling {node.name}, valid: {self.module.validate()}")
        # self.module.print()

        self.in_wasm_function = False
        self.var_stack = []

    from ._imports import visit_Import, visit_ImportFrom

    from ._variables import visit_Constant, visit_Name

    def visit_Return(self, node: Return):
        if not self.in_wasm_function:
            raise NotImplementedError

        value = super().visit(node.value)
        return self.module.Return(value)

    def visit_BinOp(self, node: BinOp):
        if not self.in_wasm_function:
            raise NotImplementedError

        left = super().visit(node.left)
        right = super().visit(node.right)
        (cast_left, cast_right) = self._cast_numeric_to_matching(
            left, right, node.lineno
        )
        op_type = cast_left.get_type()

        match node.op:
            case ast.Add():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.AddInt32()
                    case binaryen.i64:
                        op = binaryen.operations.AddInt64()
                    case binaryen.f32:
                        op = binaryen.operations.AddFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.AddFloat64()
                    case _:
                        raise RuntimeError("Can't add non numeric wasm types")
            case ast.Sub():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.SubInt32()
                    case binaryen.i64:
                        op = binaryen.operations.SubInt64()
                    case binaryen.f32:
                        op = binaryen.operations.SubFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.SubFloat64()
                    case _:
                        raise RuntimeError("Can't subtract non numeric wasm types")
            case ast.Mult():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.MulInt32()
                    case binaryen.i64:
                        op = binaryen.operations.MulInt64()
                    case binaryen.f32:
                        op = binaryen.operations.MulFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.MulFloat64()
                    case _:
                        raise RuntimeError("Can't multiply non numeric wasm types")
            case ast.Mod():
                match op_type:
                    # TODO: Assuming signed
                    case binaryen.i32:
                        op = binaryen.operations.RemSInt32()
                    case binaryen.i64:
                        op = binaryen.operations.RemSInt64()
                    case _:
                        raise RuntimeError("Can't do modulus on non integer wasm types")
            case ast.FloorDiv():
                match op_type:
                    # TODO: Assuming signed
                    case binaryen.i32:
                        op = binaryen.operations.DivSInt32()
                    case binaryen.i64:
                        op = binaryen.operations.DivSInt64()
                    case binaryen.f32:
                        op = binaryen.operations.DivFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.DivFloat64()
                    case _:
                        raise RuntimeError("Can't multiply non numeric wasm types")
            case (
                ast.MatMult()
                | ast.Div()
                | ast.Pow()
                | ast.LShift()
                | ast.RShift()
                | ast.BitOr()
                | ast.BitXor()
                | ast.BitAnd()
            ):
                raise NotImplementedError
            case _:
                raise NotImplementedError

        return self.module.binary(op, cast_left, cast_right)

    def visit_If(self, node: If):
        if not self.in_wasm_function:
            raise NotImplementedError

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

    def visit_While(self, node: ast.While):
        if not self.in_wasm_function:
            raise NotImplementedError

        if len(node.orelse) != 0:
            raise NotImplementedError

        self.while_stack.append(id(node))

        loop_body_expressions = []
        for python_exp in node.body:
            wasm_exp = super().visit(python_exp)
            loop_body_expressions.append(wasm_exp)

        cur_id = self.while_stack.pop()

        test = super().visit(node.test)

        restart_loop = self.module.Break(f"loop_{cur_id}".encode("ascii"), None, None)

        body = self.module.block(
            f"loop_body_{cur_id}".encode("ascii"),
            [*loop_body_expressions, restart_loop],
            binaryen.none,
        )

        loop_test = self.module.If(test, body, self.module.nop())

        loop = self.module.loop(f"loop_{cur_id}".encode("ascii"), loop_test)

        return loop

    def visit_Compare(self, node: Compare):
        if len(node.comparators) > 1 or len(node.ops) > 1:
            # TODO: Supported chained comparisons
            print(
                "Error: Chained comparisons e.g. 1 <= a < 10 are not currently supported. Please use brackets."
            )
            raise NotImplementedError

        if not self.in_wasm_function:
            raise NotImplementedError

        left = super().visit(node.left)
        right = super().visit(node.comparators[0])
        (cast_left, cast_right) = self._cast_numeric_to_matching(
            left, right, node.lineno
        )
        op_type = cast_left.get_type()

        # TODO: Don't assume signed
        match node.ops[0]:
            case ast.Eq():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.EqInt32()
                    case binaryen.i64:
                        op = binaryen.operations.EqInt64()
                    case binaryen.f32:
                        op = binaryen.operations.EqFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.EqFloat64()
                    case _:
                        raise RuntimeError("Can't equate non numeric wasm types")
            case ast.NotEq():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.NeInt32()
                    case binaryen.i64:
                        op = binaryen.operations.NeInt64()
                    case binaryen.f32:
                        op = binaryen.operations.NeFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.NeFloat64()
                    case _:
                        raise RuntimeError("Can't not-equate non numeric wasm types")
            case ast.Lt():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.LtSInt32()
                    case binaryen.i64:
                        op = binaryen.operations.LtSInt64()
                    case binaryen.f32:
                        op = binaryen.operations.LtFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.LtFloat64()
                    case _:
                        raise RuntimeError("Can't add non numeric wasm types")
            case ast.LtE():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.LeSInt32()
                    case binaryen.i64:
                        op = binaryen.operations.LeSInt64()
                    case binaryen.f32:
                        op = binaryen.operations.LeFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.LeFloat64()
                    case _:
                        raise RuntimeError(
                            "Can't less than or equal non numeric wasm types"
                        )
            case ast.Gt():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.GtSInt32()
                    case binaryen.i64:
                        op = binaryen.operations.GtSInt64()
                    case binaryen.f32:
                        op = binaryen.operations.GtFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.GtFloat64()
                    case _:
                        raise RuntimeError("Can't greater than non numeric wasm types")
            case ast.GtE():
                match op_type:
                    case binaryen.i32:
                        op = binaryen.operations.GeSInt32()
                    case binaryen.i64:
                        op = binaryen.operations.GeSInt64()
                    case binaryen.f32:
                        op = binaryen.operations.GeFloat32()
                    case binaryen.f64:
                        op = binaryen.operations.GeFloat64()
                    case _:
                        raise RuntimeError(
                            "Can't greater than or equal non numeric wasm types"
                        )
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

        return self.module.binary(op, cast_left, cast_right)

    def visit_Call(self, node: Call):
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
        raise RuntimeError(
            f"Node of type {node.__class__.__name__} is not supported by pygwasm. Line number {node.lineno if hasattr(node, 'lineno') else '?'}"
        )
