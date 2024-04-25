from ast import AnnAssign, Call, Name
from typing import TYPE_CHECKING

import binaryen

from .pre_compiler import get_binaryen_type

if TYPE_CHECKING:
    from .compiler import Compiler

# WARNING: This module redefines built in functions such as len() ! Do not use them or import them because they will give you the Wasm version


def list(compiler: "Compiler", node: Call):
    if not compiler.gc:
        raise RuntimeError("Enable Garbage Collection with the -gc flag to use arrays")

    if node.args.__len__() != 1:
        raise RuntimeError

    func = node.args[0]
    mod = compiler.module

    match func:
        case Call(func=Name(id="range")):
            if not isinstance(node.parent, AnnAssign):
                print(f"Parent is actually {node.parent}")
                raise RuntimeError()
            array_type = get_binaryen_type(
                node.parent.annotation, compiler.object_aliases
            )
            array_element_type = binaryen.type.array_type.get_element_type(array_type)

            start = mod.i32(0)
            stop: binaryen.Expression
            step = mod.i32(1)
            if func.args.__len__() == 1:
                stop = compiler.visit(func.args[0])
            if func.args.__len__() >= 2:
                start = compiler.visit(func.args[0])
                stop = compiler.visit(func.args[1])
            if func.args.__len__() == 3:
                step = compiler.visit(func.args[2])

            start = compiler._cast_numeric_to_type(
                start, binaryen.type.Int32, node.lineno
            )
            stop = compiler._cast_numeric_to_type(
                stop, binaryen.type.Int32, node.lineno
            )
            step = compiler._cast_numeric_to_type(
                step, binaryen.type.Int32, node.lineno
            )

            # create array with length ceil((stop - start)/step) == ((stop - start) + step - 1) / step;
            # source: https://stackoverflow.com/questions/2745074/fast-ceiling-of-an-integer-division-in-c-c
            minus_op = binaryen.operations.SubInt32()
            add_op = binaryen.operations.AddInt32()
            one = mod.i32(1)

            stop_sub_start = mod.binary(minus_op, stop, start)

            div_op = binaryen.operations.DivFloat64()
            div_step = mod.binary(
                div_op,
                compiler._cast_numeric_to_type(
                    stop_sub_start, binaryen.type.Float64, node.lineno
                ),
                compiler._cast_numeric_to_type(
                    step, binaryen.type.Float64, node.lineno
                ),
            )

            ceil_op = binaryen.operations.CeilFloat64()
            ceil_f = mod.unary(ceil_op, div_step)

            array_len = compiler._cast_numeric_to_type(
                ceil_f, binaryen.type.Int32, node.lineno
            )

            zero = compiler._cast_numeric_to_type(
                mod.i32(0), array_element_type, node.lineno
            )
            array_create = mod.array_new(array_type, array_len, zero)  #!!!!
            array = compiler.func_ref.add_var(array_create.get_type())
            init_array = mod.local_set(array, array_create)
            get_array = mod.local_get(array, array_create.get_type())

            loop_name = f"range_{id(node)}".encode("ascii")

            # create variable n i32
            n = compiler.func_ref.add_var(binaryen.type.Int32)
            init_n = mod.local_set(n, mod.i32(0))  #!!!!
            # create variable i matching type and value to start
            i = compiler.func_ref.add_var(binaryen.type.Int32)
            init_i = mod.local_set(i, start)  #!!!!
            get_i = mod.local_get(i, binaryen.type.Int32)

            # i <= stop
            lte = binaryen.operations.LtSInt32()
            loop_condition = mod.binary(lte, get_i, stop)

            restart_loop = mod.Break(loop_name, None, None)

            # set array[n] = i,  i + step, restart_loop
            body = mod.block(
                None,
                [
                    mod.array_set(
                        get_array,
                        mod.local_get(n, binaryen.type.Int32),
                        compiler._cast_numeric_to_type(
                            get_i, array_element_type, node.lineno
                        ),
                    ),
                    mod.local_set(i, mod.binary(add_op, get_i, step)),
                    mod.local_set(
                        n,
                        mod.binary(
                            add_op, mod.local_get(n, binaryen.type.Int32), mod.i32(1)
                        ),
                    ),
                    restart_loop,
                ],
                binaryen.type.TypeNone,
            )

            loop_test = mod.If(loop_condition, body, None)

            loop = mod.loop(loop_name, loop_test)

            return_array = get_array

            main_body = mod.block(
                None,
                [init_array, init_n, init_i, loop, return_array],
                binaryen.type.TypeNone,
            )
            return main_body
        case _:
            raise RuntimeError()


def len(compiler: "Compiler", node: Call):
    if not compiler.gc:
        raise RuntimeError("Enable Garbage Collection with the -gc flag to use arrays")

    if node.args.__len__() != 1:
        raise RuntimeError

    match node.func:
        case Name(id="len"):
            # Assuming its a array
            value = compiler.visit(node.args[0])
            return compiler.module.array_len(value)
