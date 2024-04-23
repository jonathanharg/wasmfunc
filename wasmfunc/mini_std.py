from ast import AnnAssign, Call, Name, Constant
from typing import TYPE_CHECKING
from .pre_compiler import get_binaryen_type
import binaryen

if TYPE_CHECKING:
    from .compiler import Compiler


def list(compiler: "Compiler", node: Call):
    if len(node.args) != 1:
        raise RuntimeError
    
    func = node.args[0]
    mod = compiler.module

    match func:
        case Call(func=Name(id="range")):
            if not isinstance(node.parent, AnnAssign):
                print(f"Parent is actually {node.parent}")
                raise RuntimeError()
            array_type = get_binaryen_type(node.parent.annotation, compiler.object_aliases)
            array_element_type = binaryen.type.array_type.get_element_type(array_type)

            start = mod.i64(0)
            stop: binaryen.Expression
            step = mod.i64(1)
            if len(func.args) == 1:
                stop = compiler.visit(func.args[0])
            if len(func.args) >= 2:
                start = compiler.visit(func.args[0])
                stop = compiler.visit(func.args[1])
            if len(func.args) == 3:
                step = compiler.visit(func.args[2])
            
            # cast all three to matching
            stop_type = stop.get_type()
            stop_is_i32 = stop_type == binaryen.type.Int32
            start = compiler._cast_numeric_to_type(start, stop_type, node.lineno)
            step = compiler._cast_numeric_to_type(step, stop_type, node.lineno)

            if stop.get_type() not in [binaryen.type.Int32, binaryen.type.Int64]:
                raise RuntimeError

            # create array with length ceil((stop - start)/step) == ((stop - start) + step - 1) / step;
            # source: https://stackoverflow.com/questions/2745074/fast-ceiling-of-an-integer-division-in-c-c
            minus_op = binaryen.operations.SubInt32() if stop_is_i32 else binaryen.operations.SubInt64()
            add_op = binaryen.operations.AddInt32() if stop_is_i32 else binaryen.operations.AddInt64()
            one = mod.i32(1) if stop_is_i32 else mod.i64(1)

            stop_sub_start = mod.binary(minus_op, stop, start)
            add_step = mod.binary(add_op, stop_sub_start, step)
            minus_one = mod.binary(minus_op, add_step, one)
            div_op = binaryen.operations.DivSInt32()
            array_len = mod.binary(div_op, minus_one, step)

            zero = compiler._cast_numeric_to_type(mod.i32(0), array_element_type, node.lineno)
            array = mod.array_new(array_type, array_len, zero) #!!!!
            
            loop_name = f"range_{id(node)}".encode('ascii')

            # create variable n i32
            n = compiler.func_ref.add_var(binaryen.type.Int32)
            init_n = mod.local_set(n, mod.i32(0)) #!!!!
            # create variable i matching type and value to start
            i = compiler.func_ref.add_var(stop_type)
            init_i = mod.local_set(i, start) #!!!!
            get_i = mod.local_get(i, stop_type)

            # i <= stop
            lte = binaryen.operations.LeSInt32() if stop_is_i32 else binaryen.operations.LeSInt64()
            loop_condition = mod.binary(lte, get_i, stop)


            restart_loop = mod.Break(loop_name, None, None)

            # set array[n] = i,  i + step, restart_loop
            body = mod.block(None, [
                mod.array_set(array, mod.local_get(n, binaryen.type.Int32), compiler._cast_numeric_to_type(get_i, array_element_type, node.lineno)),
                mod.local_set(i, mod.binary(add_op, get_i, step)),
                restart_loop
            ], binaryen.type.TypeNone)

            loop_test = mod.If(loop_condition, body, None)

            loop = mod.loop(loop_name, loop_test)

            return_array = array

            main_body = mod.block(None, [
                array,
                init_n,
                init_i,
                loop,
                return_array
            ], binaryen.type.TypeNone)
            return main_body
        case _:
            raise RuntimeError()

