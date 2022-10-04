import typing as t


START = object()
END = object()
DIRTY = object()


C = t.TypeVar('C')
T = t.TypeVar('T')


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


class ComponentsTopology(t.Generic[C], t.Collection[t.Tuple[str, C]]):

    def __init__(self):
        self._vertexes = {}
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

    def add(self, name: str, component, before=END, after=START):
        self._edge(after, name)
        self._edge(name, before)
        self._vertexes[name] = component

    def __contains__(self, name: str) -> bool:
        return name in self._vertexes

    def __len__(self) -> int:
        return len(self._vertexes)

    def __delitem__(self, name: str):
        del self._graph[name]
        del self._vextexes[name]
        for frm, targets in self._graph.items():
            if name in targets:
                targets.remove(name)
        self._order = DIRTY

    @staticmethod
    def sort(graph: t.Mapping[str, str], node: str) -> t.Deque[str]:
        result = t.Deque()
        seen = set()

        def visiter(node):
            for target in graph[node]:
                if target not in seen:
                    seen.add(target)
                    visiter(target)
            result.appendleft(node)

        visiter(node)
        return result

    @property
    def sorted(self) -> t.Sequence[t.Tuple[str, C]]:
        if self._sorted is DIRTY:
            self._sorted = tuple(
                (name, self._vertexes[name])
                for name in self.sort(self._graph, START)
                if name not in (START, END)
            )
        return self._sorted

    def __iter__(self) -> t.Iterable[t.Tuple[str, C]]:
        return iter(self.sorted)

    def __reversed__(self) -> t.Iterable[t.Tuple[str, C]]:
        return reversed(self.sorted)
