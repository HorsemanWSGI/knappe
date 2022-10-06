import typing as t
from collections.abc import Hashable


C = t.TypeVar('C', bound=Hashable)
T = t.TypeVar('T', covariant=True)


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
