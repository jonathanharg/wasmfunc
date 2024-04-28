#!/usr/bin/env python
import ast
from ast import (
    AST,
    Add,
    AnnAssign,
    Assert,
    Assign,
    Attribute,
    AugAssign,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    Break,
    Call,
    Compare,
    Constant,
    Continue,
    Del,
    Div,
    Eq,
    Expr,
    FloorDiv,
    FunctionDef,
    Global,
    Gt,
    GtE,
    If,
    IfExp,
    Import,
    ImportFrom,
    In,
    Invert,
    Is,
    IsNot,
    List,
    Load,
    LShift,
    Lt,
    LtE,
    MatMult,
    Mod,
    Module,
    Mult,
    Name,
    NodeTransformer,
    NodeVisitor,
    Not,
    NotEq,
    NotIn,
    Pass,
    Pow,
    Return,
    RShift,
    Slice,
    Store,
    Sub,
    Subscript,
    UAdd,
    UnaryOp,
    USub,
    While,
)

import binaryen

from . import mini_std
from .pre_compiler import (
    does_contain_wasm,
    get_binaryen_type,
    handle_Import,
    handle_ImportFrom,
)

type BinaryenType = binaryen.internals.BinaryenType
Int32 = binaryen.type.Int32
Int64 = binaryen.type.Int64
Float32 = binaryen.type.Float32
Float64 = binaryen.type.Float64


class Compiler(NodeVisitor):
    def __init__(
        self,
        filename: str,
        function_arguments: dict[str, BinaryenType],
        function_return: dict[str, BinaryenType],
        enable_gc=False,
        enable_str=False,
    ) -> None:
        self.filename = filename
        self.module = binaryen.Module()
        self.module_aliases = []
        self.object_aliases = {}

        self.func_ref: binaryen.FunctionRef | None = None
        self.function_arguments = function_arguments
        self.function_returns = function_return

        self.variable_types: dict[str, BinaryenType] = {}
        self.variable_indexes: dict[str, int] = {}

        self.all_globals: dict[str, tuple[BinaryenType, AST]] = {}
        self.scoped_globals: dict[str, BinaryenType] = {}

        self.while_stack = [0]

        if enable_gc:
            print("Warning: using WasmGC, this is experimental")
            self.module.set_feature(
                binaryen.Feature.GC | binaryen.Feature.ReferenceTypes
            )

        if enable_str:
            self.module.set_feature(
                binaryen.Feature.GC
                | binaryen.Feature.ReferenceTypes
                | binaryen.Feature.Strings
            )
            enable_gc = True
            print("Warning: using Strings, this is experimental")

        self.gc = enable_gc
        self.str = enable_str
        super().__init__()

    def _create_local(self, name: str, var_type: BinaryenType) -> int:
        if name in self.variable_types:
            raise RuntimeError("A local already exists with this name.")
        index = self.func_ref.add_var(var_type)
        self.variable_types[name] = var_type
        self.variable_indexes[name] = index
        self.func_ref.set_local_name(index, name.encode("ascii"))
        return index

    def _cast_numeric_to_matching(
        self, left: binaryen.Expression, right: binaryen.Expression, lineno: int
    ):
        left_type = left.get_type()
        right_type = right.get_type()
        input_types = [left_type, right_type]

        number_types = [Int32, Int64, Float32, Float64]
        large_types = [Int64, Float64]
        float_types = [Float32, Float64]

        if any(map(lambda x: x not in number_types, input_types)):
            raise RuntimeError("Unsupported types in number operation")

        if left_type == right_type:
            return (left, right)

        # print(f"Warning: performing runtime casting on line {lineno}")

        large = any(map(lambda x: x in large_types, input_types))
        floating = any(map(lambda x: x in float_types, input_types))

        if floating:
            target_type = Float64 if large else Float32
        else:
            target_type = Int64 if large else Int32

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
        convert_to: BinaryenType,
        lineno: int,
    ):
        from_type = target.get_type()
        match from_type:
            case binaryen.type.Int32:
                match convert_to:
                    case binaryen.type.Int32:
                        return None
                    case binaryen.type.Int64:
                        return binaryen.operations.ExtendSInt32()
                    case binaryen.type.Float32:
                        return binaryen.operations.ConvertSInt32ToFloat32()
                    case binaryen.type.Float64:
                        return binaryen.operations.ConvertSInt32ToFloat64()
                    case _:
                        raise RuntimeError(
                            f"Can't convert from int32 to required type on line {lineno}"
                        )
            case binaryen.type.Int64:
                match convert_to:
                    case binaryen.type.Int32:
                        return binaryen.operations.WrapInt64()
                    case binaryen.type.Int64:
                        return None
                    case binaryen.type.Float32:
                        return binaryen.operations.ConvertSInt64ToFloat32()
                    case binaryen.type.Float64:
                        return binaryen.operations.ConvertSInt64ToFloat64()
                    case _:
                        raise RuntimeError(
                            f"Can't convert from int64 to required type on line {lineno}"
                        )
            case binaryen.type.Float32:
                match convert_to:
                    case binaryen.type.Int32:
                        return binaryen.operations.TruncSFloat32ToInt32()
                    case binaryen.type.Int64:
                        return binaryen.operations.TruncSFloat32ToInt64()
                    case binaryen.type.Float32:
                        return None
                    case binaryen.type.Float64:
                        return binaryen.operations.PromoteFloat32()
                    case _:
                        raise RuntimeError(
                            f"Can't convert from float32 to required type on line {lineno}"
                        )
            case binaryen.type.Float64:
                match convert_to:
                    case binaryen.type.Int32:
                        return binaryen.operations.TruncSFloat64ToInt32()
                    case binaryen.type.Int64:
                        return binaryen.operations.TruncSFloat64ToInt64()
                    case binaryen.type.Float32:
                        return binaryen.operations.DemoteFloat64()
                    case binaryen.type.Float64:
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
        convert_to: BinaryenType,
        lineno: int,
    ):
        if not binaryen.type.heap_type.is_basic(convert_to):  # type: ignore
            print("Warning cannot cast heap types")
            return target

        op = self._get_numeric_conversion_op(target, convert_to, lineno)
        if op is None:
            return target
        # print(
        #     f"INFO: Casting {binaryen.type.to_str(target.get_type())} to {binaryen.type.to_str(convert_to)} on line {lineno}"
        # )
        return self.module.unary(op, target)

    def _set_var(
        self,
        name: str,
        value: binaryen.Expression,
        lineno: int,
        type_annotation: BinaryenType | None = None,
    ):
        if type_annotation is None:
            if name in self.variable_types:
                type_annotation = self.variable_types[name]
            if name in self.scoped_globals:
                type_annotation = self.scoped_globals[name]

        if type_annotation is not None:
            value = self._cast_numeric_to_type(value, type_annotation, lineno)

        if name in self.variable_types:
            if (
                type_annotation is not None
                and self.variable_types[name] != type_annotation
            ):
                raise RuntimeError(
                    f'You cannot change the type of a variable when reassigning. "{self.filename}", line {lineno}.'
                )

            return self.module.local_set(self.variable_indexes[name], value)

        if name in self.scoped_globals:
            if (
                type_annotation is not None
                and self.scoped_globals[name] != type_annotation
            ):
                raise RuntimeError(
                    f'Cannot change the type of a global variable after initialisation. "{self.filename}", line {lineno}.'
                )
            return self.module.global_set(name.encode("ascii"), value)

        # Must be a new local
        if type_annotation is None:
            type_annotation = value.get_type()

        if (
            not binaryen.type.heap_type.is_basic(type_annotation)
            and not self.str
            and self.gc
        ):
            type_annotation = binaryen.type.from_heap_type(type_annotation, True)

        local_id = self._create_local(name, type_annotation)
        return self.module.local_set(local_id, value)

    def visit_Module(self, node: Module):
        # Add a parent attribute to all nodes
        for n in ast.walk(node):
            for child in ast.iter_child_nodes(n):
                child.parent = n

        super().generic_visit(node)

    def visit(self, node):
        # print(f"Visiting: {node}")
        return super().visit(node)

    # visit_Expression
    # visit_FunctionType

    def visit_FunctionDef(self, node: FunctionDef):
        """Check if function has the binaryen decorator @binaryen.wasmfunc"""
        contains_wasm = does_contain_wasm(
            node, self.object_aliases, self.module_aliases
        )

        if not contains_wasm:
            return

        if self.func_ref is not None:
            # We are already in a WASM function, inner functions are not supported
            raise NotImplementedError

        name = bytes(node.name, "ascii")

        if node.args.kwarg:
            raise RuntimeError("kwargs not supported")
        if any(default for default in node.args.defaults):
            raise RuntimeError("Defaults not supported")

        for i, argument in enumerate(node.args.args):
            argument_type = get_binaryen_type(argument.annotation, self.object_aliases)
            if argument_type is None:
                raise RuntimeError(
                    f'Types must be provided for all function arguments. "{self.filename}", line {node.lineno}.'
                )

            self.variable_types[argument.arg] = argument_type
            self.variable_indexes[argument.arg] = i

        return_type = get_binaryen_type(node.returns, self.object_aliases)

        if return_type is None:
            return_type = binaryen.type.TypeNone

        body = self.module.block(None, [], return_type)

        # # Dicts preserve insertion order, no locals have been added yet
        function_parameter_types = list(self.variable_types.values())

        self.func_ref = self.module.add_function(
            name,
            binaryen.type.create(function_parameter_types),
            return_type,
            [],
            body,
        )

        for i, argument in enumerate(node.args.args):
            self.func_ref.set_local_name(i, argument.arg.encode("ascii"))

        for body_node in node.body:
            if isinstance(body_node, AST):
                expression = self.visit(body_node)
                if isinstance(expression, binaryen.Expression):
                    body.append_child(expression)
                elif expression is not None:
                    print("Error: Non binaryen output of node!")

        self.module.add_function_export(name, name)

        self.func_ref = None
        self.variable_indexes = {}
        self.variable_types = {}
        self.scoped_globals = {}

    # visit_AsyncFunctionDef
    # visit_ClassDef

    def visit_Return(self, node: Return):
        if self.func_ref is None:
            return None

        value = self.visit(node.value) if node.value is not None else None

        current_func_name = binaryen.ffi.string(self.func_ref.get_name()).decode(
            "utf-8"
        )
        return_type = self.function_returns[current_func_name]

        casted_value = self._cast_numeric_to_type(value, return_type, node.lineno)
        return self.module.Return(casted_value)

    # visit_Delete

    def visit_Assign(self, node: Assign):
        if self.func_ref is None:
            if isinstance(node.value, Name) and node.value.id in self.all_globals:
                raise RuntimeError(
                    f'Cannot modify the value of a WebAssembly global outside of a WebAssembly function. "{self.filename}", line {node.lineno}.'
                )
            return

        value = self.visit(node.value)
        if not isinstance(value, binaryen.Expression):
            raise RuntimeError(
                f'Expected Binaryen value when visiting assign value. "{self.filename}", line {node.lineno}.'
            )

        expressions = []
        for target in node.targets:
            match target:
                case Name():
                    name = target.id
                    expressions.append(self._set_var(name, value, target.lineno))
                case Subscript(value=Name()):
                    if not self.gc:
                        raise RuntimeError(
                            "Enable Garbage Collection with the -gc flag to use arrays"
                        )
                    # Assume its a list
                    name = target.value.id

                    index = self.visit(target.slice)
                    index = self._cast_numeric_to_type(index, Int32, node.lineno)

                    array_type = self.variable_types[name]
                    array_index = self.variable_indexes[name]

                    array_heap_type = binaryen.type.get_heap_type(array_type)
                    array_element_type = binaryen.type.array_type.get_element_type(
                        array_heap_type
                    )
                    array_value = self._cast_numeric_to_type(
                        value, array_element_type, node.lineno
                    )

                    array_expression = self.module.local_get(array_index, array_type)
                    expressions.append(
                        self.module.array_set(array_expression, index, array_value)
                    )

                case _:
                    raise RuntimeError(
                        f'Variable unpacking, subscripts and annotations are not supported. "{self.filename}", line {node.lineno}.'
                    )

        if len(expressions) > 1:
            return self.module.block(None, expressions, binaryen.type.TypeNone)

        return expressions[0]

    # visit_TypeAlias

    def visit_AugAssign(self, node: AugAssign):
        if self.func_ref is None:
            return None

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

    def visit_AnnAssign(self, node: AnnAssign):
        if self.func_ref is None:
            # Variable may be a global, so we should track it.

            type_annotation = get_binaryen_type(node.annotation, self.object_aliases)

            if type_annotation is None:
                return

            if node.value is None:
                raise RuntimeError(
                    f'Global variables must be initialised with a value. "{self.filename}", line {node.lineno}.'
                )

            if not isinstance(node.target, Name):
                raise RuntimeError(
                    f'Global variables are not supported for attributes or subscripts. "{self.filename}", line {node.lineno}.'
                )

            if node.target.id in self.all_globals:
                raise RuntimeError(
                    f'Cannot modify the value of a WebAssembly global outside of a WebAssembly function. "{self.filename}", line {node.lineno}.'
                )

            global_name = node.target.id

            self.all_globals[global_name] = (type_annotation, node.value)
            return

        if not isinstance(node.target, Name):
            raise RuntimeError(
                f'Variables are not supported for attributes or subscripts. "{self.filename}", line {node.lineno}.'
            )

        if not node.simple:
            # A node is not simple if it uses tuples, attributes or subscripts
            # e.g. (a): int = 1, a.b: int, a[1]: int
            raise NotImplementedError

        type_annotation = get_binaryen_type(node.annotation, self.object_aliases)
        if type_annotation is None:
            raise RuntimeError(
                f'Unknown Wasm type. "{self.filename}", line {node.lineno}.'
            )

        if node.value is None:
            raise RuntimeError(
                f'A variable must be initialised to a value. "{self.filename}", line {node.lineno}.'
            )

        value = self.visit(node.value)

        return self._set_var(
            node.target.id, value, node.lineno, type_annotation=type_annotation
        )

    # visit_For
    # visit_AsyncFor

    def visit_While(self, node: While):
        if self.func_ref is None:
            return None

        loop_condition = self.visit(node.test)

        self.while_stack.append(id(node))

        loop_body = []
        for python_exp in node.body:
            wasm_exp = self.visit(python_exp)
            loop_body.append(wasm_exp)

        cur_id = self.while_stack.pop()

        else_body = []
        for python_exp in node.orelse:
            wasm_exp = self.visit(python_exp)
            else_body.append(wasm_exp)

        else_block = (
            self.module.block(
                f"loop_else_{cur_id}".encode("ascii"),
                else_body,
                binaryen.type.TypeNone,
            )
            if len(else_body) > 0
            else self.module.nop()
        )

        restart_loop = self.module.Break(f"loop_{cur_id}".encode("ascii"), None, None)

        body = self.module.block(
            f"loop_body_{cur_id}".encode("ascii"),
            [*loop_body, restart_loop],
            binaryen.type.TypeNone,
        )

        loop_test = self.module.If(loop_condition, body, else_block)

        loop = self.module.loop(f"loop_{cur_id}".encode("ascii"), loop_test)

        return loop

    def visit_If(self, node: If):
        if self.func_ref is None:
            return None

        condition = self.visit(node.test)

        if_true = self.module.block(None, [], binaryen.type.Auto)
        if_false = self.module.block(None, [], binaryen.type.Auto)

        for python_exp in node.body:
            wasm_exp = self.visit(python_exp)
            if_true.append_child(wasm_exp)

        for python_exp in node.orelse:
            wasm_exp = self.visit(python_exp)
            if_false.append_child(wasm_exp)

        return self.module.If(condition, if_true, if_false)

    # visit_With
    # visit_AsyncWith
    # visit_Match
    # visit_Raise
    # visit_Try
    # visit_TryStar

    def visit_Assert(self, node: Assert):
        if self.func_ref is None:
            return None

        if node.msg is not None:
            raise RuntimeError("Assertion messages are not supported")

        condition = self.visit(node.test)
        check = self.module.If(condition, self.module.nop(), self.module.unreachable())
        return check

    def visit_Import(self, node: Import):
        handle_Import(node, self.module_aliases)

    def visit_ImportFrom(self, node: ImportFrom):
        handle_ImportFrom(node, self.object_aliases)

    def visit_Global(self, node: Global):
        for name in node.names:
            if name not in self.all_globals:
                # We have no record of a global
                raise RuntimeError(
                    "Global variable not initialised. You must initialise global variables at the top level with a Wasm type."
                )

            binaryen_type = self.all_globals[name][0]
            ascii_name = name.encode("ascii")
            existing_global = self.module.get_global(ascii_name)

            if existing_global is None:
                value_python = self.all_globals[name][1]
                if isinstance(value_python, Constant) and isinstance(
                    value_python.value, (int, float)
                ):
                    value = None

                    if binaryen_type == binaryen.type.Int32:
                        self.module.add_global(
                            ascii_name,
                            binaryen_type,
                            True,
                            self.module.i32(value_python.value),
                        )
                    if binaryen_type == binaryen.type.Int64:
                        self.module.add_global(
                            ascii_name,
                            binaryen_type,
                            True,
                            self.module.i64(value_python.value),
                        )
                    if binaryen_type == binaryen.type.Float32:
                        self.module.add_global(
                            ascii_name,
                            binaryen_type,
                            True,
                            self.module.f32(value_python.value),
                        )
                    if binaryen_type == binaryen.type.Float64:
                        self.module.add_global(
                            ascii_name,
                            binaryen_type,
                            True,
                            self.module.f64(value_python.value),
                        )
                else:
                    print(
                        f'Warning! Global initialisations should be constant. Trying to visit the value, this will probably fail!  "{self.filename}", line {node.lineno}.'
                    )
                    value = self.visit(value_python)
                    cast_value = self._cast_numeric_to_type(
                        value, binaryen_type, node.lineno
                    )
                    self.module.add_global(ascii_name, binaryen_type, True, cast_value)

            # promote from possible to loaded global
            self.scoped_globals[name] = binaryen_type

        return

    # visit_Nonlocal
    def visit_Expr(self, node: Expr):
        if self.func_ref is None:
            return None

        value = self.visit(node.value)
        assert isinstance(value, binaryen.Expression)
        if value.get_type() != binaryen.type.TypeNone:
            return self.module.drop(value)
        return value

    def visit_Pass(self, _: Pass):
        if self.func_ref is None:
            return None

        return self.module.nop()

    def visit_Break(self, _: Break):
        if self.func_ref is None:
            return None

        if len(self.while_stack) == 0:
            raise RuntimeError("Break can only be used in a while loop")
        loop_id = self.while_stack[-1]
        loop_name = f"loop_body_{loop_id}".encode("ascii")
        return self.module.Break(loop_name, None, None)

    def visit_Continue(self, _: Continue):
        if self.func_ref is None:
            return None

        if len(self.while_stack) == 0:
            raise RuntimeError("Break can only be used in a while loop")
        loop_id = self.while_stack[-1]
        loop_name = f"loop_{loop_id}".encode("ascii")
        return self.module.Break(loop_name, None, None)

    # visit_BoolOp
    # visit_NamedExpr

    def visit_BinOp(self, node: BinOp):
        if self.func_ref is None:
            return None

        left = self.visit(node.left)
        right = self.visit(node.right)
        (cast_left, cast_right) = self._cast_numeric_to_matching(
            left, right, node.lineno
        )
        op_type = cast_left.get_type()

        match node.op:
            case Add():
                match op_type:
                    case binaryen.type.Int32:
                        add_op = binaryen.operations.AddInt32()
                    case binaryen.type.Int64:
                        add_op = binaryen.operations.AddInt64()
                    case binaryen.type.Float32:
                        add_op = binaryen.operations.AddFloat32()
                    case binaryen.type.Float64:
                        add_op = binaryen.operations.AddFloat64()
                    case _:
                        raise RuntimeError("Can't add non numeric wasm types")
                return self.module.binary(add_op, cast_left, cast_right)
            case Sub():
                match op_type:
                    case binaryen.type.Int32:
                        sub_op = binaryen.operations.SubInt32()
                    case binaryen.type.Int64:
                        sub_op = binaryen.operations.SubInt64()
                    case binaryen.type.Float32:
                        sub_op = binaryen.operations.SubFloat32()
                    case binaryen.type.Float64:
                        sub_op = binaryen.operations.SubFloat64()
                    case _:
                        raise RuntimeError("Can't subtract non numeric wasm types")
                return self.module.binary(sub_op, cast_left, cast_right)
            case Mult():
                match op_type:
                    case binaryen.type.Int32:
                        mult_op = binaryen.operations.MulInt32()
                    case binaryen.type.Int64:
                        mult_op = binaryen.operations.MulInt64()
                    case binaryen.type.Float32:
                        mult_op = binaryen.operations.MulFloat32()
                    case binaryen.type.Float64:
                        mult_op = binaryen.operations.MulFloat64()
                    case _:
                        raise RuntimeError("Can't multiply non numeric wasm types")
                return self.module.binary(mult_op, cast_left, cast_right)
            case Div():
                match op_type:
                    case binaryen.type.Int32:
                        return self.module.binary(
                            binaryen.operations.DivSInt32(), cast_left, cast_right
                        )
                    case binaryen.type.Int64:
                        return self.module.binary(
                            binaryen.operations.DivSInt64(), cast_left, cast_right
                        )
                    case binaryen.type.Float32:
                        return self.module.binary(
                            binaryen.operations.DivFloat32(), cast_left, cast_right
                        )
                    case binaryen.type.Float64:
                        return self.module.binary(
                            binaryen.operations.DivFloat64(), cast_left, cast_right
                        )
                    case _:
                        raise RuntimeError("Can't multiply non numeric wasm types")
            case Mod():
                match op_type:
                    case binaryen.type.Int32:
                        mod_op = binaryen.operations.RemSInt32()
                    case binaryen.type.Int64:
                        mod_op = binaryen.operations.RemSInt64()
                    case _:
                        raise RuntimeError("Can't do modulus on non integer wasm types")
                return self.module.binary(mod_op, cast_left, cast_right)
            case FloorDiv():
                # NOTE: Python has strange floor division because of PEP 238
                # In python: a // b == floor(a/b)
                left_float = self._cast_numeric_to_type(
                    left, binaryen.type.Float64, node.lineno
                )
                right_float = self._cast_numeric_to_type(
                    right, binaryen.type.Float64, node.lineno
                )
                result = self.module.binary(
                    binaryen.operations.DivFloat64(), left_float, right_float
                )
                return self.module.unary(binaryen.operations.FloorFloat64(), result)
            case (
                MatMult() | Pow() | LShift() | RShift() | BitOr() | BitXor() | BitAnd()
            ):
                raise NotImplementedError
            case _:
                raise NotImplementedError

    def visit_UnaryOp(self, node: UnaryOp):
        if self.func_ref is None:
            return None

        value = self.visit(node.operand)
        op_type = value.get_type()
        match node.op:
            case UAdd():
                # Unary Add does nothing
                return value
            case USub():
                match op_type:
                    case binaryen.type.Int32:
                        return self.module.binary(
                            binaryen.operations.MulInt32(), self.module.i32(-1), value
                        )
                    case binaryen.type.Int64:
                        return self.module.binary(
                            binaryen.operations.MulInt64(), self.module.i64(-1), value
                        )
                    case binaryen.type.Float32:
                        return self.module.unary(
                            binaryen.operations.NegFloat32(), value
                        )
                    case binaryen.type.Float64:
                        return self.module.unary(
                            binaryen.operations.NegFloat64(), value
                        )
                    case _:
                        raise RuntimeError(
                            "Can't do unary subtraction on non numeric wasm types"
                        )
            case Not():
                zero = self.module.i32(0)
                zero = self._cast_numeric_to_type(zero, op_type, node.lineno)
                if op_type == Int32:
                    op = binaryen.operations.SubInt32()
                elif op_type == Int64:
                    op = binaryen.operations.SubInt64()
                else:
                    raise RuntimeError
                return self.module.binary(op, zero, value)
            case Invert():
                raise NotImplementedError

    # visit_Lambda
    # visit_IfExp

    def visit_IfExp(self, node: IfExp):
        if self.func_ref is None:
            return None

        condition = self.visit(node.test)
        if_true = self.visit(node.body)
        if_false = self.visit(node.orelse)
        return self.module.select(condition, if_true, if_false, binaryen.type.Auto)

    # visit_Dict
    # visit_Set
    # visit_ListComp
    # visit_SetComp
    # visit_DictComp
    # visit_GeneratorExp
    # visit_Await
    # visit_Yield
    # visit_YieldFrom

    def visit_Compare(self, node: Compare):
        if self.func_ref is None:
            return None

        if len(node.comparators) > 1 or len(node.ops) > 1:
            # TODO: Supported chained comparisons
            raise NotImplementedError(
                "Error: Chained comparisons e.g. 1 <= a < 10 are not currently supported. Please use brackets."
            )

        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        (cast_left, cast_right) = self._cast_numeric_to_matching(
            left, right, node.lineno
        )
        op_type = cast_left.get_type()

        match node.ops[0]:
            case Eq():
                match op_type:
                    case binaryen.type.Int32:
                        op = binaryen.operations.EqInt32()
                    case binaryen.type.Int64:
                        op = binaryen.operations.EqInt64()
                    case binaryen.type.Float32:
                        op = binaryen.operations.EqFloat32()
                    case binaryen.type.Float64:
                        op = binaryen.operations.EqFloat64()
                    case _:
                        raise RuntimeError("Can't equate non numeric wasm types")
            case NotEq():
                match op_type:
                    case binaryen.type.Int32:
                        op = binaryen.operations.NeInt32()
                    case binaryen.type.Int64:
                        op = binaryen.operations.NeInt64()
                    case binaryen.type.Float32:
                        op = binaryen.operations.NeFloat32()
                    case binaryen.type.Float64:
                        op = binaryen.operations.NeFloat64()
                    case _:
                        raise RuntimeError("Can't not-equate non numeric wasm types")
            case Lt():
                match op_type:
                    case binaryen.type.Int32:
                        op = binaryen.operations.LtSInt32()
                    case binaryen.type.Int64:
                        op = binaryen.operations.LtSInt64()
                    case binaryen.type.Float32:
                        op = binaryen.operations.LtFloat32()
                    case binaryen.type.Float64:
                        op = binaryen.operations.LtFloat64()
                    case _:
                        raise RuntimeError("Can't add non numeric wasm types")
            case LtE():
                match op_type:
                    case binaryen.type.Int32:
                        op = binaryen.operations.LeSInt32()
                    case binaryen.type.Int64:
                        op = binaryen.operations.LeSInt64()
                    case binaryen.type.Float32:
                        op = binaryen.operations.LeFloat32()
                    case binaryen.type.Float64:
                        op = binaryen.operations.LeFloat64()
                    case _:
                        raise RuntimeError(
                            "Can't less than or equal non numeric wasm types"
                        )
            case Gt():
                match op_type:
                    case binaryen.type.Int32:
                        op = binaryen.operations.GtSInt32()
                    case binaryen.type.Int64:
                        op = binaryen.operations.GtSInt64()
                    case binaryen.type.Float32:
                        op = binaryen.operations.GtFloat32()
                    case binaryen.type.Float64:
                        op = binaryen.operations.GtFloat64()
                    case _:
                        raise RuntimeError("Can't greater than non numeric wasm types")
            case GtE():
                match op_type:
                    case binaryen.type.Int32:
                        op = binaryen.operations.GeSInt32()
                    case binaryen.type.Int64:
                        op = binaryen.operations.GeSInt64()
                    case binaryen.type.Float32:
                        op = binaryen.operations.GeFloat32()
                    case binaryen.type.Float64:
                        op = binaryen.operations.GeFloat64()
                    case _:
                        raise RuntimeError(
                            "Can't greater than or equal non numeric wasm types"
                        )
            case Is():
                raise NotImplementedError
            case IsNot():
                raise NotImplementedError
            case In():
                raise NotImplementedError
            case NotIn():
                raise NotImplementedError
            case _:
                raise NotImplementedError

        return self.module.binary(op, cast_left, cast_right)

    def visit_Call(self, node: Call):
        if self.func_ref is None:
            return None

        if len(node.keywords) > 0:
            raise NotImplementedError("wasmfunc does not support keyword arguments!")

        assert isinstance(node.func, Name)

        if node.func.id not in self.function_arguments:
            if hasattr(mini_std, node.func.id):
                return getattr(mini_std, node.func.id)(self, node)
            else:
                raise RuntimeError(f"Function not found {node.func.id}")

        name = bytes(node.func.id, "ascii")

        argument_types = self.function_arguments[node.func.id]

        args = []
        for i, argument in enumerate(node.args):
            arg_exp = self.visit(argument)
            arg_type = argument_types[i]
            cast_arg_exp = self._cast_numeric_to_type(arg_exp, arg_type, node.lineno)
            args.append(cast_arg_exp)

        return_type = self.function_returns[node.func.id]

        return self.module.call(name, args, return_type)

    # visit_FormattedValue
    # visit_JoinedStr

    def visit_Constant(self, node: Constant):
        if self.func_ref is None:
            return None
        if node.value is None:
            raise NotImplementedError
        if isinstance(node.value, str):
            return self.module.string_const(node.value.encode("ascii"))
        if isinstance(node.value, int):
            value = binaryen.literal.int32(node.value)
            return self.module.const(value)
        if isinstance(node.value, float):
            value = binaryen.literal.float64(node.value)
            return self.module.const(value)
        # From the docs:
        # The values represented can be simple types such as a number, string or None, but also immutable container types (tuples and frozensets) if all of their elements are constant.
        raise NotImplementedError

    # visit_Attribute

    def visit_Subscript(self, node: Subscript):
        if self.func_ref is None:
            return None
        if not self.gc:
            raise RuntimeError(
                "Enable Garbage Collection with the -gc flag to use arrays"
            )

        value = self.visit(node.value)
        if not isinstance(value, binaryen.Expression):
            raise RuntimeError("Expected Binaryen Expression for subscript value")

        index = self.visit(node.slice)
        # TODO: MATCH ON SLICE

        if not isinstance(index, binaryen.Expression):
            raise RuntimeError("Expected Binaryen Expression for index value")

        index = self._cast_numeric_to_type(index, Int32, node.lineno)

        value_type = value.get_type()
        value_heap_type = binaryen.type.get_heap_type(value_type)

        match node.ctx:
            case Load():
                if binaryen.type.heap_type.is_array(value_heap_type):
                    return self.module.array_get(
                        value, index, binaryen.type.Auto, False
                    )
                raise NotImplementedError(
                    f"Cannot load subscript on {value_type} ({value_heap_type})"
                )
            case Store():
                print(f"SUBSCRIPT PARENT IS {node.parent}")
                print(f"REACHED LEGACY CODE")
                return (value, index)
            case Del():
                raise NotImplementedError("Cannot delete with subscript")

    # visit_Starred

    def visit_Name(self, node: Name):
        if self.func_ref is None:
            return None

        if isinstance(node.ctx, Load):
            if node.id in self.variable_types:
                index = self.variable_indexes[node.id]
                var_type = self.variable_types[node.id]
                return self.module.local_get(index, var_type)

            if node.id in self.scoped_globals:
                ascii_name = node.id.encode("ascii")
                binaryen_type = self.scoped_globals[node.id]
                return self.module.global_get(ascii_name, binaryen_type)

            raise RuntimeError(f"Trying to load an undeclared variable {node.id}")
        if isinstance(node.ctx, Store):
            raise RuntimeError("This code should never be reached")
        if isinstance(node.ctx, Del):
            raise NotImplementedError

    def visit_List(self, node: List):
        if self.func_ref is None:
            return None
        if not self.gc:
            raise RuntimeError(
                "Enable Garbage Collection with the -gc flag to use arrays"
            )

        if not isinstance(node.parent, AnnAssign):
            raise RuntimeError("Lists must be assigned with an annotation.")
        array_type = get_binaryen_type(node.parent.annotation, self.object_aliases)
        array_element_type = binaryen.type.array_type.get_element_type(array_type)

        elements = []
        for element in node.elts:
            wasm_element = self.visit(element)
            cast_element = self._cast_numeric_to_type(
                wasm_element, array_element_type, node.lineno
            )
            elements.append(cast_element)

        return self.module.array_new_fixed(array_type, elements)

    # visit_Tuple
    # visit_Slice

    def generic_visit(self, node):
        if self.func_ref is None:
            return None
        raise RuntimeError(
            f"Node of type {node.__class__.__name__} is not supported by wasmfunc. Line number {node.lineno if hasattr(node, 'lineno') else '?'}"
        )
