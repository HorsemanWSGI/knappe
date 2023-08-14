import pytest
from unittest.mock import Mock
from frozendict import frozendict
from knappe import routing
from knappe.plugins import Plugin, event
from knappe.response import Response
from knappe.meta import Route


class Application:
    pass


class RoutingApplication:

    def __init__(self):
        self.router = routing.Router()


def test_empty_plugin():
    plugin = Plugin('my empty plugin')
    assert plugin.dependencies == ()
    assert plugin.components is None


def test_empty_lineage():
    plugin = Plugin('1')
    plugin1 = Plugin('2', dependencies=[plugin])
    plugin2 = Plugin('3', dependencies=[plugin, plugin1])
    assert plugin.__lineage__ == (plugin,)
    assert plugin1.__lineage__ == (plugin, plugin1)
    assert plugin2.__lineage__ == (plugin, plugin1, plugin2)


def test_plugin_install():
    app = Application()
    plugin = Plugin('my empty plugin')
    plugin.install(app)
    assert app.__installed_plugins__ == {'my empty plugin'}

    # No duplication.
    plugin.install(app)
    assert app.__installed_plugins__ == {'my empty plugin'}


def test_plugin_install_func():

    def func():
        pass

    plugin = Plugin('my empty plugin')
    plugin.install(func)
    assert func.__installed_plugins__ == {'my empty plugin'}

    # No duplication.
    plugin.install(func)
    assert func.__installed_plugins__ == {'my empty plugin'}


def test_plugin_install_with_hooks():

    tracker = Mock()
    app = Application()
    plugin = Plugin('my empty plugin')

    @plugin.subscribe(event.before_install)
    def installer(plugin, app):
        tracker(plugin, app)

    plugin.install(app)
    tracker.assert_called_once_with(plugin, app)
    tracker.reset_mock()

    # Only installed once
    plugin.install(app)
    tracker.assert_not_called()


def test_plugin_with_blueprint_no_registry():
    router = routing.Router()
    plugin = Plugin('route', components={"router": router})
    app = Application()

    with pytest.raises(LookupError):
        plugin.install(app)


def test_plugin_with_singular_blueprint():
    router = routing.Router()
    plugin = Plugin('route', components={"router": router})
    app = RoutingApplication()

    @router.register('/')
    def handler(request):
        return Response(200, body='ok')

    plugin.install(app)
    assert dict(app.router) == {
        ('/', 'GET'): Route.create(
            identifier="/",
            value=handler,
            method='GET'
        )
    }


def test_plugin_on_func():
    router = routing.Router()
    plugin = Plugin('route', components={"router": router})

    def func():
        """This is a non-sense example.
        """

    func.router = routing.Router()

    @router.register('/')
    def handler(request):
        return Response(200, body='ok')

    plugin.install(func)
    assert dict(func.router) == {
        ('/', 'GET'): Route.create(
            identifier="/",
            value=handler,
            method='GET'
        )
    }
