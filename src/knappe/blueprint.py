import inspect
import itertools
import typing as t
import inspect_mate
from types import MethodType, FunctionType


R = t.TypeVar('R')
R_co = t.TypeVar('R_co', bound=R)


class Call:

    __slots__ = ('name', 'params', 'decorated')

    name: str
    params: inspect.BoundArguments
    decorated: t.Optional[t.Callable]

    def __init__(self, name, params, decorated=None):
        self.name = name
        self.params = params
        self.decorated = decorated

    def __repr__(self):
        if self.decorated is not None:
            return (f"<Decorator {self.name!r} " +
                    f"for {self.decorated} with {self.params}>")
        return (f"<Call {self.name!r} with {self.params}>")


class Blueprint(t.Generic[R]):
    """A blueprint is a call buffer for registries.
    Registries are usually components that use decorator
    to register something.
    """
    __slots__ = (
        '_bound', '_calls', '_signatures',
        '_decorable_functions', '_decorable_methods',
    )

    _bound: t.Type[R]
    _calls: t.List[Call]
    _signatures: t.Dict[str, inspect.Signature]
    _decorable_functions : t.Mapping[str, t.Callable]
    _decorable_methods : t.Mapping[str, t.Callable]

    def __init__(self, bound: t.Type[R]):
        self._calls = []
        self._bound = bound
        self._signatures = {}
        self._decorable_functions = dict(
            inspect_mate.get_static_methods(self._bound)
        )
        self._decorable_methods = dict(itertools.chain(
            inspect_mate.get_regular_methods(self._bound),
            inspect_mate.get_class_methods(self._bound)
        ))

    def __iter__(self) -> t.Iterator[Call]:
        return iter(self._calls)

    def apply_to(self, registry: R_co):
        for call in self._calls:
            target = getattr(registry, call.name)
            result = target(*call.params.args, **call.params.kwargs)
            if call.decorated is not None:
                result(call.decorated)

    def __getattr__(self, name: str):
        sig = self._signatures.get(name)
        if sig is None:
            if func := self._decorable_functions.get(name):
                sig = self._signatures[name] = inspect.signature(func)
            elif func := self._decorable_methods.get(name):
                parameters = list(
                    inspect.signature(func).parameters.values())
                sig = self._signatures[name] = inspect.Signature(
                    parameters[1:]  # pop self/cls
                )
            else:
                raise AttributeError(
                    f'{name} is not a function or method.')

        def call_registration(*args, **kwargs):
            params = sig.bind(*args, **kwargs)
            call = Call(name, params)
            self._calls.append(call)
            def as_decorator(func: t.Callable):
                call.decorated = func
                return func
            return as_decorator

        return call_registration
