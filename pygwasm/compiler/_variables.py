from ast import Constant, Del, Load, Name, Store
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import Compiler

import binaryen


def visit_Name(self: "Compiler", node: Name) -> binaryen.Expression | None:
    var = self._get_local_by_name(node.id)

    if var is None:
        raise RuntimeError

    (index, var_type) = var

    if isinstance(node.ctx, Load):
        return self.module.local_get(index, var_type)
    if isinstance(node.ctx, Store):
        raise NotImplementedError
    if isinstance(node.ctx, Del):
        raise NotImplementedError


def visit_Constant(self: "Compiler", node: Constant) -> Any:
    if node.value is None:
        raise NotImplementedError
    if isinstance(node.value, str):
        raise NotImplementedError
    if isinstance(node.value, int):
        # TODO: Should probably bounds check this!!!
        # TODO: This should be explicit! Explicitly decide on int32 signed/unsigned
        return self.module.const(binaryen.lib.BinaryenLiteralInt32(node.value))
    if isinstance(node.value, float):
        return self.module.const(binaryen.lib.BinaryenLiteralFloat32(node.value))
    # From the docs:
    # The values represented can be simple types such as a number, string or None, but also immutable container types (tuples and frozensets) if all of their elements are constant.
    raise NotImplementedError
