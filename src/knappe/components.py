import typing as t
from abc import ABC, abstractmethod
from collections import UserList, UserDict
from dataclasses import dataclass, field
from enum import Enum
from frozendict import frozendict
from plum import Signature
from plum.resolver import Resolver
from prejudice.errors import ConstraintsErrors
from prejudice.types import Predicate
from prejudice.utils import resolve_constraints
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

    def check(self, *args, **kwargs) -> bool:
        if self.conditions:
            if errors := self.evaluate(*args, **kwargs):
                return False
        return True

    def ensure(self, *args, **kwargs):
        if self.conditions:
            if errors := self.evaluate(*args, **kwargs):
                raise errors

    def __call__(self, *args, **kwargs):
        if not isinstance(self.value, t.Callable):
            raise ValueError(f'{self.value} is not callable.')
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


class Collection(t.Generic[C], Components[C], UserList[C]):

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
        names = set()
        for component in super().find_all(*args, Lookup.ALL):
            if component.identifier not in names:
                names.add(component.identifier)
                yield component

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


# import typing as t
# from zope.interface import Interface
# from zope.interface import providedBy, implementedBy
# from zope.interface.interfaces import ISpecification
# from zope.interface.adapter import AdapterRegistry


# def interfaces(requirements):
#     ifaces = []
#     for requirement in requirements:
#         if ISpecification.providedBy(requirement):
#             ifaces.append(requirement)
#             continue
#         if isinstance(requirement, type):
#             ifaces.append(implementedBy(requirement))
#         else:
#             raise TypeError("Sources must either be "
#                             "an interface or a class.")
#     return ifaces


# class ComponentRegistry:

#     def __init__(self):
#         self.registry = AdapterRegistry()

#     def register(self, sources, target, name, component):
#         required = interfaces(sources)
#         self.registry.register(required, target, name, component)

#     def subscribe(self, sources, target, component):
#         required = interfaces(sources)
#         self.registry.subscribe(required, target, component)

#     def lookup(self, obs, target, name):
#         return self.registry.lookup(map(providedBy, obs), target, name)

#     def cls_lookup(self, classes, target, name):
#         return self.registry.lookup(
#             map(implementedBy, classes), target, name
#         )

#     def lookup_all(self, obs, target):
#         return iter(self.registry.lookupAll(
#             list(map(providedBy, obs)), target))

#     def subscriptions(self, obs, target):
#         return self.registry.subscriptions(
#             map(providedBy, obs), target
#         )

#     def predicates(self, classes, target):
#         return self.registry.subscriptions(
#             map(implementedBy, classes), target
#         )


# class Registry:
#     _registry: ComponentRegistry
#     factory: t.ClassVar[t.Type[C]] = Component

#     class resolve_to(Interface):
#         pass

#     def __init__(self, *args):
#         self._registry = ComponentRegistry()
#         super().__init__(*args)

#     def register(self, discriminant: t.Iterable[t.Type], name, *args, **kwargs):
#         def register_component(value):
#             from uuid import uuid4

#             item = self.factory.create(
#                 value, name, *args, **kwargs)

#             self._registry.subscribe(
#                 discriminant, self.resolve_to, item
#             )
#             return value
#         return register_component

#     def find_one(self, *args, name=''):
#         raise NotImplementedError()

#     def find_all(self, *args):
#         yield from self._registry.subscriptions(args, self.resolve_to)


# class NamedRegistry:
#     _registry: ComponentRegistry
#     factory: t.ClassVar[t.Type[C]] = Component

#     class resolve_to(Interface):
#         pass

#     def __init__(self, *args):
#         self._registry = ComponentRegistry()
#         super().__init__(*args)

#     def register(self, discriminant: t.Iterable[t.Type], *args, name='', **kwargs):
#         def register_component(value):
#             from uuid import uuid4

#             item = self.factory.create(
#                 value, name, *args, **kwargs)

#             self._registry.register(
#                 discriminant, self.resolve_to, item.identifier, item
#             )
#             return value
#         return register_component

#     def find_one(self, *args, name=''):
#         return self._registry.lookup(args, self.resolve_to, name)

#     def find_all(self, *args):
#         for name, item in self._registry.lookup_all(args, self.resolve_to):
#             yield item
