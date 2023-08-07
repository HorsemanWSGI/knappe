import typing as t
from collections import UserList, UserDict
from plum.resolver import Resolver
from .meta import Component, K, T


C = t.TypeVar('C', bound=Component)


class ComponentsRegistry(t.Generic[C], ABC):

    factory: t.Type[C] = Component

    @abstractmethod
    def add(self, component: C):
        pass

    def spawn(self,
              value: T,
              identifier: K,
              name: str = '',
              title: str = '',
              description: str = '',
              conditions: t.Optional[t.Iterable[Predicate]] = None,
              classifiers: t.Optional[t.Iterable[str]] = None,
              **metadata: t.Any
              ):

        if classifiers is None:
            classifiers = ()

        if conditions is None:
            conditions = ()

        return self.factory(
            identifier=identifier,
            name=name,
            title=title,
            value=value,
            classifiers=frozenset(classifiers),
            conditions=tuple(conditions),
            metadata=metadata
        )

    def create(self, value, *args, **kwargs):
        component = self.spawn(value, *args, **kwargs)
        self.add(component)
        return component

    def register(self, *args, **kwargs):
        def register_resolver(func):
            self.create(func, *args, **kwargs)
            return func
        return register_resolver


class ComponentsCollection(
        t.Generic[C], ComponentsRegistry[C], UserList):

    def add(self, component: I):
        self.append(component)

    def __or__(self, other):
        return self.__class__([*self, *other])


class ComponentsMapping(
        t.Generic[K, C], ComponentsRegistry[C], UserDict[K, C]):

    def add(self, component: C):
        self[component.identifier] = component


class SignatureRegistry(ComponentsMapping[Signature, C]):

    def __init__(self, *args, **kwargs):
        self.resolver: Resolver = Resolver()
        super().__init__(*args, **kwargs)

    def __setitem__(self, signature: Signature, component: C):
        self.resolver.register(component.identifier)
        super().__setitem__(signature, component)

    def match_all(self, *args):
        found = []
        for signature, component in self.items():
            if signature.match(args):
                found.append(component)
        return sorted(found, key=lambda component: component.identifier)

    def lookup(self, *args):
        match = self.resolver.resolve(args)
        return self[match]

    def cast(self, *args, **kwargs):
        component = self.lookup(*args)
        return component(*args, **kwargs)
