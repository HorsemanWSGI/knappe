import typing as t
from collections.abc import Hashable


START = object()
END = object()
DIRTY = object()


C = t.TypeVar('C', bound=Hashable, covariant=True)
T = t.TypeVar('T', covariant=True)


class TypeMapping(t.Generic[T, C], t.Dict[t.Type[T], t.List[C]]):

    __slots__ = ()

    def add(self, cls: t.Type[T], component: C) -> t.NoReturn:
        components = self.setdefault(cls, [])
        components.append(component)

    @staticmethod
    def lineage(cls: t.Type[T]):
        yield from cls.__mro__

    def lookup(self, cls: t.Type[T]) -> t.Iterator[C]:
        for parent in self.lineage(cls):
            if parent in self:
                yield from self[parent]


class ComponentsTopology(t.Generic[C], t.Collection[C]):

    def __init__(self):
        self._graph = {START: set(), END: set()}
        self._sorted = DIRTY

    def _edge(self, frm: str, to: str):
        if frm is END:
            raise ValueError('')
        if to is START:
            raise ValueError('')

        vectors = self._graph.setdefault(frm, set())
        vectors.add(to)
        self._order = DIRTY

    def add(self, component: C, before=END, after=START):
        self._edge(after, component)
        self._edge(component, before)
        self._sorted = DIRTY

    def __contains__(self, component: C) -> bool:
        return component in self._graph

    def __len__(self) -> int:
        return len(self.sorted)

    @staticmethod
    def sort(graph: t.Mapping[C, t.Set[C]], node: C) -> t.Deque[C]:
        result = t.Deque()
        seen = set()

        def visiter(node):
            for target in graph[node]:
                if target not in seen:
                   seen.add(target)
                   visiter(target)
            result.appendleft(node)

        visiter(node)
        if len(result) != len(graph):
            raise RuntimeError('Sort loop detected.')
        return result

    @property
    def sorted(self) -> t.Sequence[C]:
        if self._sorted is DIRTY:
            self._sorted = tuple(
                component
                for component in self.sort(self._graph, START)
                if component not in (START, END)
            )
        return self._sorted

    def __iter__(self) -> t.Iterable[C]:
        return iter(self.sorted)

    def __reversed__(self) -> t.Iterable[C]:
        return reversed(self.sorted)
