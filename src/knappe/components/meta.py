import typing as t
from types import MappingProxyType
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from prejudice.errors import ConstraintError, ConstraintsErrors
from prejudice.types import Predicate
from prejudice.utils import resolve_constraints
from plum import Signature
from plum.resolver import Resolver
from collections import UserList, UserDict
from ..collections import PriorityChain
from frozendict import frozendict


T = t.TypeVar('T')
K = t.TypeVar('K', bound=t.Hashable)


def immutable_mapping(mapping: t.Optional[t.Mapping] = None):
    if mapping is None:
        mapping = {}
    return MappingProxyType(mapping)


@dataclass
class Component(t.Generic[K, T]):
    value: T
    identifier: K
    name: str = ''
    title: str = ''
    description: str = ''
    conditions: t.Tuple[Predicate] = field(default_factory=tuple)
    classifiers: t.FrozenSet[str] = field(default_factory=frozenset)
    metadata: t.Mapping[str, t.Any] = field(default_factory=frozendict)

    def evaluate(self, *args, **kwargs) -> t.Optional[ConstraintsErrors]:
        return resolve_constraints(self.conditions, self, *args, **kwargs)

    def __call__(self, *args, silence_errors=True, **kwargs):
        if not isinstance(self.value, t.Callable):
            raise ValueError(f'{self.value} is not callable.')
        if errors := self.evaluate(*args, **kwargs):
            if not silence_errors:
                raise errors
        else:
            return self.value(*args, **kwargs)

    @classmethod
    def create(cls,
               value: T,
               identifier: K,
               name: str = '',
               title: str = '',
               description: str = '',
               conditions: t.Optional[t.Iterable[Predicate]] = None,
               classifiers: t.Optional[t.Iterable[str]] = None,
               metadata: t.Mapping[str, t.Any] = None,
               **kwargs
               ):

        return cls(
            identifier=identifier,
            name=name,
            title=title,
            value=value,
            classifiers=frozenset(classifiers or ()),
            conditions=tuple(conditions or ()),
            metadata=frozendict(metadata or {}),
            **kwargs
        )


C = t.TypeVar('C', bound=Component)


class Components(t.Generic[C], ABC):

    factory: t.Type[C] = Component

    @abstractmethod
    def add(self, component: C):
        pass

    def create(self, value, *args, **kwargs):
        component = self.factory.create(value, *args, **kwargs)
        self.add(component)
        return component

    def register(self, *args, **kwargs):
        def register_resolver(func):
            self.create(func, *args, **kwargs)
            return func
        return register_resolver


class Collection(t.Generic[C], Components[C], UserList):

    def add(self, component: C):
        self.append(component)

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__([*self, *other])


class Mapping(t.Generic[K, C], Components[C], UserDict[K, C]):

    def add(self, component: C):
        self[component.identifier] = component


class Registry(t.Generic[C], Mapping[Signature, C]):

    factory: t.ClassVar[t.Type[C]] = Component

    __slots__ = ('_resolver', '_ordered')

    def __init__(self, *components: t.Iterable[t.Tuple[Signature, C]]):
        self._ordered: PriorityChain[Signature, C] = PriorityChain()
        self._resolver: Resolver = Resolver()
        super().__init__(components)

    def __setitem__(self, signature: Signature, component: C):
        self._ordered.add(component, signature)
        self._resolver.register(signature)
        super().__setitem__(signature, component)

    def __delitem__(self, signature):
        component = self[signature]
        super.__delitem__(signature)
        del self._ordered[(signature, component)]

    def find_one(self, *args):
        match = self.resolver.resolve(args)
        return self[match]

    def find_all(self, *args):
        for signature, component in self._ordered:
            if signature.match(args):
                yield component

    def register(self, signature: Signature, *args, **kwargs):
        def register_component(value):
            self[signature] = self.factory.create(value, *args, **kwargs)
            return value
        return register_resolver

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(self._ordered | other._ordered)
