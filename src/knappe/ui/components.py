import typing as t
from plum import Signature
from horseman.meta import Overhead
from chameleon.zpt import template
from ozg.items import ItemResolver
from ozg.templates import Templates
from ozg.components.actions import Actions


DEFAULT = ""
Default = t.Literal[DEFAULT]


class NamedComponent:

    store: ItemResolver

    def __init__(self, store: t.Optional[ItemResolver] = None):
        if store is None:
            store = ItemResolver()
        self.store = store

    def create(self,
               value: t.Any,
               discriminant: t.Iterable[t.Type],
               name: str | Default,
               **kwargs):
        signature = Signature(t.Literal[name], *discriminant)
        return self.store.create(value, signature, name=name, **kwargs)

    def get(self, *args, name=""):
        return self.store.lookup(name, *args)

    def register(self, name: str | Default, discriminant: t.Iterable[t.Type], **kws):
        def register_component(func):
            self.create(func, discriminant, name=name, **kws)
            return func
        return register_component

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(self.store | other.store)
