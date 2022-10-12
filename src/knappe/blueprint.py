import copy
import inspect
import itertools
import typing as t
import inspect_mate
from frozendict import frozendict
from ordered_set import OrderedSet
from types import MethodType, FunctionType


R = t.TypeVar('R')
R_co = t.TypeVar('R_co', bound=R)


class ProxyCall(t.NamedTuple):
    name: str
    args: t.Iterable[t.Any]
    kwargs: t.Mapping[str, t.Any]
    decorated: t.Optional[t.Callable] = None

    def __repr__(self):
        if self.decorated is not None:
            return (f"<ProxyDecorator {self.name!r} " +
                    f"for {self.decorated} with {self.params}>")
        return (f"<ProxyCall {self.name!r} with {self.params}>")


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
    _calls: t.MutableSet[ProxyCall]
    _signatures: t.Dict[str, inspect.Signature]
    _decorable_functions : t.Mapping[str, t.Callable]
    _decorable_methods : t.Mapping[str, t.Callable]

    def __init__(self, bound: t.Type[R]):
        self._calls = OrderedSet()
        self._bound = bound
        self._signatures = {}
        self._decorable_functions = frozendict(
            inspect_mate.get_static_methods(self._bound)
        )
        self._decorable_methods = frozendict(itertools.chain(
            inspect_mate.get_regular_methods(self._bound),
            inspect_mate.get_class_methods(self._bound)
        ))

    def __iter__(self) -> t.Iterator[ProxyCall]:
        return iter(self._calls)

    def __or__(self, other):
        if not isinstance(self, other.__class__):
            raise TypeError(
                f'Cannot merge {self.__class__} and {other.__class__}.')
        if not issubclass(other._bound, self._bound):
            raise TypeError(
                f'Blueprint bound types {self._bound} and {other._bound}'
                + f' are incompatible. {other._bound} must be of type '
                + f'{self._bound} or a superclass of it.'
            )
        copied = copy.copy(self)
        copied._signatures = copied._signatures | other._signatures
        copied._calls = copied._calls | other._calls
        return copied

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
            call = ProxyCall(
                name,
                args=tuple(params.args),
                kwargs=frozendict(params.kwargs)
            )
            self._calls.add(call)
            def as_decorator(func: t.Callable):
                self._calls.remove(call)
                self._calls.add(call._replace(decorated=func))
                return func
            return as_decorator

        return call_registration


def apply_blueprint(blueprint: Blueprint[R], registry: R_co):
    if not isinstance(registry, blueprint._bound):
        raise TypeError(
            f'{registry!r} should be of type {blueprint._bound}')
    for call in blueprint:
        target = getattr(registry, call.name)
        result = target(*call.args, **call.kwargs)
        if call.decorated is not None:
            result(call.decorated)
