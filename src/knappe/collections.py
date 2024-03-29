import bisect
import typing as t
from collections.abc import Hashable


C = t.TypeVar('C', bound=Hashable)
S = t.TypeVar('S')

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


class PriorityChain(t.Generic[S]):

    __slots__ = ('_chain',)

    _chain: t.List[S]

    def __init__(self, *items: t.Iterable[S]):
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

    def add(self, sortable: S):
        if not self._chain:
            self._chain = [sortable]
        else:
            bisect.insort(self._chain, sortable)

    def remove(self, sortable: S):
        if sortable not in self._chain:
            raise KeyError('{sortable!r} does not exist.')
        self._chain.remove(sortable)

    def clear(self):
        self._chain.clear()
