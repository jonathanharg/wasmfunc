from typing import Protocol, Self, Union


class PygwasmBaseType(Protocol):
    pass


class i32(PygwasmBaseType, Protocol):
    def __add__(self, __value: Union[Self, int], /) -> Self: ...
    def __sub__(self, __value: Union[Self, int], /) -> Self: ...
    def __lt__(self, __value: Union[Self, int], /) -> bool: ...
    def __le__(self, __value: Union[Self, int], /) -> bool: ...
    def __eq__(self, __value: Union[Self, int], /) -> bool: ...
    def __gt__(self, __value: Union[Self, int], /) -> bool: ...


class i64(PygwasmBaseType, Protocol):
    def __add__(self, __value: Union[Self, int], /) -> Self: ...
    def __sub__(self, __value: Union[Self, int], /) -> Self: ...
    def __lt__(self, __value: Union[Self, int], /) -> bool: ...
    def __le__(self, __value: Union[Self, int], /) -> bool: ...
    def __eq__(self, __value: Union[Self, int], /) -> bool: ...
    def __gt__(self, __value: Union[Self, int], /) -> bool: ...


class f32(PygwasmBaseType, Protocol):
    def __add__(self, __value: Union[Self, int], /) -> Self: ...
    def __sub__(self, __value: Union[Self, int], /) -> Self: ...
    def __lt__(self, __value: Union[Self, int], /) -> bool: ...
    def __le__(self, __value: Union[Self, int], /) -> bool: ...
    def __eq__(self, __value: Union[Self, int], /) -> bool: ...
    def __gt__(self, __value: Union[Self, int], /) -> bool: ...


class f64(PygwasmBaseType, Protocol):
    def __add__(self, __value: Union[Self, int], /) -> Self: ...
    def __sub__(self, __value: Union[Self, int], /) -> Self: ...
    def __lt__(self, __value: Union[Self, int], /) -> bool: ...
    def __le__(self, __value: Union[Self, int], /) -> bool: ...
    def __eq__(self, __value: Union[Self, int], /) -> bool: ...
    def __gt__(self, __value: Union[Self, int], /) -> bool: ...


class none(PygwasmBaseType):
    pass
