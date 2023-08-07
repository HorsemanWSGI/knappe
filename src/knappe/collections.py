import typing as t
from collections.abc import Hashable


C = t.TypeVar('C', bound=Hashable)
T = t.TypeVar('T', covariant=True)
S = t.TypeVar('S')


class TypeMapping(t.Generic[T, C], t.Dict[t.Type[T], t.List[C]]):

    __slots__ = ()

    def add(self, cls: t.Type[T], component: C):
        components = self.setdefault(cls, [])
        components.append(component)

    @staticmethod
    def lineage(cls: t.Type[T]):
        yield from cls.__mro__

    def lookup(self, cls: t.Type[T]) -> t.Iterator[C]:
        for parent in self.lineage(cls):
            if parent in self:
                yield from self[parent]


Marker = t.NewType('Marker', str)
Node = t.Union[C, Marker]
START = Marker('start')
END = Marker('end')


class ComponentsTopology(t.Generic[C], t.Collection[C]):

    _graph: t.MutableMapping[Node, t.Set[Node]]
    _sorted: t.Optional[t.Sequence[C]]

    def __init__(self):
        self._graph = {START: set(), END: set()}
        self._sorted = None

    def _edge(self, frm: Node, to: Node):
        if frm is END:
            raise ValueError('')
        if to is START:
            raise ValueError('')

        vectors = self._graph.setdefault(frm, set())
        vectors.add(to)

    def add(self,
            component: C,
            before: t.Union[C, Marker] = END,
            after: t.Union[C, Marker] = START):
        self._edge(after, component)
        self._edge(component, before)
        self._sorted = None

    def __contains__(self, component) -> bool:
        return component in self.sorted

    def __len__(self) -> int:
        return len(self.sorted)

    @staticmethod
    def sort(graph: t.Mapping[Node, t.Set[Node]], node: Node) -> t.Deque[C]:
        result: t.Deque[C] = t.Deque()
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
        if self._sorted is None:
            self._sorted = tuple(
                component
                for component in self.sort(self._graph, START)
                if component not in (START, END)
            )
        return self._sorted

    def __iter__(self) -> t.Iterator[C]:
        return iter(self.sorted)


class PriorityChain(t.Generic[S, C]):

    __slots__ = ('_chain',)

    _chain: t.List[t.Tuple[S, C]]

    def __init__(self, *items: t.Iterable[t.Tuple[S, C]]):
        self._chain = list(items)

    def __iter__(self):
        return iter(self._chain)

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"Unsupported merge between {self.__class__!r} "
                f"and {other.__class__!r}"
            )
        return self.__class__(*[*self._chain, *other._chain])

    def add(self, item: C, sortable: S):
        insert = (sortable, item)
        if not self._chain:
            self._chain = [insert]
        elif insert in self._chain:
            raise KeyError('Item {item!r} already exists as {sortable!r}.')
        else:
            bisect.insort(self._chain, insert)

    def remove(self, item: C, sortable: S):
        insert = (sortable, item)
        if insert not in self._chain:
            raise KeyError('Item {item!r} doest not exist as {sortable!r}.')
        self._chain.remove(insert)

    def clear(self):
        self._chain.clear()
