from ast import Import, ImportFrom
from typing import Any

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Compiler

def visit_Import(self: 'Compiler', node: Import) -> Any:
    # Record if pygwasm is imported, or if its imported under an alias
    for module in node.names:
        print(f"Found import for {module.name}")
        if module.name == "pygwasm":
            if module.asname is not None:
                print(f"Appending alias {module.asname}")
                self.module_aliases.append(module.asname)
            else:
                print("Appending default alias")
                self.module_aliases.append("pygwasm")
    return

def visit_ImportFrom(self: 'Compiler', node: ImportFrom) -> Any:
    # Record if the pygwasm decorator is imported, or if its imported under an alias
    if node.module != "pygwasm":
        print("Found non binaryen import from")
        return
    for function in node.names:
        if function.asname is not None:
            # Here we may have clashes. e.g. import i32 as integer and then reimports i64 as integer
            # This will cause issues, but if you're is doing this, you have bigger problems going on.
            self.object_aliases[function.asname] = function.name
        else:
            # Add the default name if no alias is specified
            self.object_aliases[function.name] = function.name
    return
