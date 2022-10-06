import pytest
import hamcrest
from knappe.collections import ComponentsTopology


def test_topology():
    topo: ComponentsTopology[str] = ComponentsTopology()
    topo.add('a')
    topo.add('b')
    topo.add('c')
    assert len(topo) == 3

    hamcrest.assert_that(
        list(topo),
        hamcrest.contains_inanyorder('a', 'b', 'c')
    )

    topo: ComponentsTopology[str] = ComponentsTopology()
    topo.add('a', after='b')
    topo.add('b', after='a')
    with pytest.raises(RuntimeError):
        list(topo)

    topo: ComponentsTopology[str] = ComponentsTopology()
    topo.add('a', after='b')
    topo.add('b', before='a')
    topo.add('c', after='a')
    assert list(topo) == ['b', 'a', 'c']
    assert len(topo) == 3


def test_object_topology():

    class Component:

        def __init__(self, name: str):
            self.name = name

        def __repr__(self):
            return f"<Component {self.name!r}>"


    a, b, c = Component('a'), Component('b'), Component('c')

    topo: ComponentsTopology[Component] = ComponentsTopology()
    topo.add(a)
    topo.add(b)
    topo.add(c)

    hamcrest.assert_that(
        list(topo),
        hamcrest.contains_inanyorder(a, b, c)
    )

    topo: ComponentsTopology[Component] = ComponentsTopology()
    topo.add(a, after=c)
    topo.add(b)
    topo.add(c, before=b)
    assert list(topo) in ([c, a, b], [c, b, a])

    d, e, f = Component('d'), Component('e'), Component('f')
    topo.add(d, before=a, after=b)
    topo.add(e, after=d)
    topo.add(f)
    components = list(topo)

    hamcrest.assert_that(
        components,
        hamcrest.contains_inanyorder(a, b, c, d, e, f)
    )
    assert components.index(d) < components.index(a)
    assert components.index(e) > components.index(d) > components.index(b)
