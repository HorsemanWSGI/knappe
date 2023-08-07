import typing as t
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from frozendict import frozendict
from collections import UserList, UserDict
from prejudice.errors import ConstraintsErrors
from prejudice.types import Predicate
from prejudice.utils import resolve_constraints
from plum import Signature
from plum.resolver import Resolver
from .collections import PriorityChain


T = t.TypeVar('T')
K = t.TypeVar('K', bound=t.Hashable)


class Lookup(Enum):
    ALL = 'all'


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
            description=description,
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
        self._ordered: PriorityChain[Signature] = PriorityChain()
        self._resolver: Resolver = Resolver()
        super().__init__(components)

    def __setitem__(self, signature: Signature, component: C):
        self._ordered.add(signature)
        self._resolver.register(signature)
        super().__setitem__(signature, component)

    def __delitem__(self, signature):
        component = self[signature]
        super().__delitem__(signature)
        del self._ordered[(signature, component)]

    def find_one(self, *args):
        match = self._resolver.resolve(args)
        return self[match]

    def find_all(self, *args):
        for signature in self._ordered:
            if signature.match(args):
                yield self[signature]

    def register(self, discriminant: t.Iterable[t.Type], *args, **kwargs):
        def register_component(value):
            signature = Signature(*discriminant)
            self[signature] = self.factory.create(
                value, hash(signature), *args, **kwargs)
            return value
        return register_component

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(self._ordered | other._ordered)


class NamedRegistry(Registry):

    def find_one(self, *args, name: str = ""):
        return super().find_one(*args, name)

    def find_all(self, *args):
        yield from super().find_all(*args, Lookup.ALL)

    def register(self, discriminant: t.Iterable[t.Type], *args, name: str = None, **kwargs):
        if name is None:
            raise NameError('A name is required.')
        def register_component(value):
            item = self.factory.create(value, name, *args, **kwargs)
            signature = Signature(
                *discriminant,
                t.Literal[item.identifier] | t.Literal[Lookup.ALL]
            )
            self[signature] = item
            return value
        return register_component
