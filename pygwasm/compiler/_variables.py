from ast import Load, Name, Store, Del, Constant
from typing import Any

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Compiler

import binaryen

def visit_Name(self: 'Compiler', node: Name) -> binaryen.Expression | None:
    # TODO: This is janky, use the built in python module
    (index, var_type) = next(
        ((i, v[1]) for i, v in enumerate(self.var_stack) if v[0] == node.id),
        (None, None),
    )
    if isinstance(node.ctx, Load):
        assert index is not None
        print("Replaced Name with binaryen type")
        return self.module.local_get(index, var_type)
    if isinstance(node.ctx, Store):
        raise NotImplementedError
    if isinstance(node.ctx, Del):
        raise NotImplementedError

def visit_Constant(self: 'Compiler', node: Constant) -> Any:
    if node.value is None:
        raise NotImplementedError
    if isinstance(node.value, str):
        raise NotImplementedError
    if isinstance(node.value, int):
        # TODO: Should probably bounds check this!!!
        # TODO: This should be explicit! Explicitly decide on int32 signed/unsigned
        return self.module.const(binaryen.lib.BinaryenLiteralInt32(node.value))
    if isinstance(node.value, float):
        raise NotImplementedError
    # From the docs:
    # The values represented can be simple types such as a number, string or None, but also immutable container types (tuples and frozensets) if all of their elements are constant.
    raise NotImplementedError
