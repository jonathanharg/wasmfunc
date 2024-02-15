from typing import  Union, overload

class PygwasmBaseType:
    pass

class i32(PygwasmBaseType):
    @overload
    def __add__(self, y: int) -> "i32":
        pass
    @overload
    def __add__(self, y: "i32") -> "i32":
        pass
    def __add__(self, y: Union["i32", int]) -> "i32":
        return self + y
    @overload
    def __sub__(self, y: int) -> "i32":
        pass
    @overload
    def __sub__(self, y: "i32") -> "i32":
        pass
    def __sub__(self, y: Union["i32", int]) -> "i32":
        return self + y

class none(PygwasmBaseType):
    pass