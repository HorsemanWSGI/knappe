import typing as t
from knappe.components import Component


def one_of(items: t.Iterable[Component], *classifiers: str
           ) -> t.Iterator[Component]:
    if not classifiers:
        raise KeyError('`one_of` takes at least one classifier.')
    classifiers = set(classifiers)
    for item in items:
        if item.classifiers & classifiers:
            yield item


def exact(items: t.Iterable[Component], *classifiers: str
          ) -> t.Iterator[Component]:
    if not classifiers:
        raise KeyError('`exact` takes at least one classifier.')
    classifiers = set(classifiers)
    for item in items:
        if classifiers == item.classifiers:
            yield item


def partial(items: t.Iterable[Component], *classifiers: str
            ) -> t.Iterator[Component]:
    if not classifiers:
        raise KeyError('`partial` takes at least one classifier.')
    classifiers = set(classifiers)
    for item in items:
        if item.classifiers >= classifiers:
            yield item
