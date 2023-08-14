import enum
import logging
import typing as t
from collections import namedtuple, defaultdict
from functools import cached_property
from knappe.components.meta import Components
from knappe.types import Application


A = t.TypeVar('A', bound=Application)
Logger = logging.getLogger(__name__)
Component = Components | t.Mapping | t.Set
Hook = t.Callable[['Plugin', A], None]


class event(enum.Enum):
    before_install = 'before_install'
    before_uninstall = 'before_uninstall'
    after_install = 'after_install'
    after_uninstall = 'after_uninstall'


def plugin_topology(plugin):

    def unfiltered_lineage():
        if not plugin.dependencies:
            return
        for dependency in plugin.dependencies:
            yield from dependency.__lineage__
            yield dependency

    seen = set()
    for parent in unfiltered_lineage():
        if parent not in seen:
            seen.add(parent)
            yield parent
    if plugin not in seen:
        yield plugin
    del seen


class Plugin(t.Generic[A]):

    name: str
    dependencies: t.Iterable[str]
    components: t.Optional[t.Mapping[str, Components]]
    _hooks: t.Dict[event, Hook]
    __lineage__: t.Sequence['Plugin']

    def __init__(
            self,
            name: str,
            components: t.Optional[t.Mapping[str, Components]] = None,
            dependencies: t.Optional[t.Iterable['Plugin']] = None):

        self.name = name
        if dependencies is None:
            self.dependencies = tuple()
        else:
            self.dependencies = tuple(dependencies)
        self._hooks = defaultdict(list)
        if components:
            self.components = namedtuple(
                'PluginComponents', components.keys())(*components.values())
        else:
            self.components = None
        self.__lineage__ = tuple(plugin_topology(self))

    def __repr__(self):
        return f'<Plugin {self.name!r}>'

    def subscribe(self, ev: event):
        def hook_subscription(hook: Hook):
            self._hooks[event(ev)].append(hook)
            return hook
        return hook_subscription

    def notify(self, ev: event, app: A):
        ev = event(ev)  # idempotent if correct.
        if ev in self._hooks:
            for hook in self._hooks[ev]:
                hook(self, app)

    def apply(self, app: A):
        if self.components:
            for name, component in self.components._asdict().items():
                trail = name.split('.')
                attr = trail[-1]
                node = app
                for stub in trail[:-1]:
                    node = getattr(node, stub)
                if not hasattr(node, attr):
                    raise LookupError(
                        f"{app!r} has no component {attr!r}.")
                setattr(node, attr, getattr(node, attr) | component)

    def install(self, app: A):
        installed = getattr(app, '__installed_plugins__', None)
        if installed is None:
            installed = app.__installed_plugins__ = set()
        elif not isinstance(installed, set):
            raise TypeError(
                'An error occured while bootstrapping the '
                f'plugins base on {app}.'
            )
        elif self.name in installed:
            Logger.debug(f'{self.name!r} already installed: skip.')
            return

        for dep in self.__lineage__:
            dep.apply(app)
        try:
            self.notify(event.before_install, app)
            self.apply(app)
        except Exception as exc:
            Logger.error(
                f"An error occured while installing plugin {self.name}.",
                exc_info=True
            )
            raise
        else:
            installed.add(self.name)
            self.notify(event.after_install, app)
            Logger.info(f"Plugin {self.name} installed with success.")
        return app

    def uninstall(self, app: A) -> A:
        raise NotImplementedError('Uninstall is not implemented.')
