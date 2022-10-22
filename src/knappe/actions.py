import typing as t
from collections import OrderedDict
from prejudice.errors import ConstraintsErrors
from prejudice.types import Predicate
from prejudice.utils import resolve_constraints
from knappe.collections import TypeMapping
from knappe.types import Request


class Action(t.NamedTuple):
    name: str
    title: str
    resolve: t.Callable
    classifiers: t.FrozenSet[str]
    attributes: t.Optional[dict] = None
    conditions: t.Optional[t.Sequence[Predicate]] = None

    def evaluate(self, *args, **kwargs) -> t.Optional[ConstraintsErrors]:
        if self.conditions:
            return resolve_constraints(
                self.conditions, self, *args, **kwargs)


class ActionStore(OrderedDict):

    def add(self,
            func: t.Callable,
            id: str,
            title: str = None,
            attributes: dict = None,
            classifiers: t.Optional[t.Iterable[str]] = None,
            conditions: t.Optional[t.Iterable[Predicate]] = None):
        if classifiers is None:
            classifiers = ()
        self[id] = Action(
            name=id,
            title=title,
            resolve=func,
            attributes=attributes,
            classifiers=frozenset(classifiers),
            conditions=tuple(conditions) if conditions else None
        )

    def register(self, *args, **kwargs):
        def register_resolver(func):
            self.add(func, *args, **kwargs)
            return func
        return register_resolver

    def partial(self, *classifiers: str) -> t.Generator[Action, None, None]:
        if not classifiers:
            raise KeyError('`partial` takes at least one classifier.')
        classifiers = set(classifiers)
        for action in self.values():
            if action.classifiers >= classifiers:
                yield action

    def exact(self, *classifiers: str) -> t.Generator[Action, None, None]:
        if not classifiers:
            raise KeyError('`exact` takes at least one classifier.')
        classifiers = set(classifiers)
        for action in self.values():
            if classifiers == action.classifiers:
                yield action

    def one_of(self, *classifiers: str) -> t.Generator[Action, None, None]:
        if not classifiers:
            raise KeyError('`one_of` takes at least one classifier.')
        classifiers = set(classifiers)
        for action in self.values():
            if action.classifiers & classifiers:
                yield


class Actions(TypeMapping[object, ActionStore]):

    @staticmethod
    def lineage(cls):
        for parent in cls.__mro__:
            if parent is object:
                break
            yield parent

    def register(self, cls, *args, **kwargs):
        actions = self.get(cls, None)
        if actions is None:
            actions = self[cls] = ActionStore()
        return actions.register(*args, **kwargs)

    def add(self, func, cls, *args, **kwargs):
        actions = self.get(cls, None)
        if actions is None:
            actions = self[cls] = ActionStore()
        return actions.add(func, *args, **kwargs)

    def get_actions_for(self, cls):
        return self.get(cls)

    def get_action_for(self, cls, name):
        if cls in self:
            actions = self[cls]
            if name in actions:
                return actions[name]

    def all_actions_for(self, cls) -> t.Iterator[Action]:
        for cls in self.lineage(cls):
            if cls in self:
                yield from self[cls].values()

    def partial(self, cls, *classifiers: str) -> t.Iterator[Action]:
        if not classifiers:
            raise KeyError('`partial` takes at least one classifier.')
        classifiers = set(classifiers)
        for cls in self.lineage(cls):
            if cls in self:
                for action in self[cls].values():
                    if action.classifiers >= classifiers:
                        yield action

    def exact(self, cls, *classifiers: str):
        if not classifiers:
            raise KeyError('`exact` takes at least one classifier.')
        classifiers = set(classifiers)
        for cls in self.lineage(cls):
            if cls in self:
                for action in self[cls].values():
                    if classifiers == action.classifiers:
                        yield action

    def one_of(self, cls,
               *classifiers: str) -> t.Generator[Action, None, None]:
        if not classifiers:
            raise KeyError('`one_of` takes at least one classifier.')
        classifiers = set(classifiers)
        for cls in self.lineage(cls):
            if cls in self:
                for action in self[cls].values():
                    if action.classifiers & classifiers:
                        yield action


class ContextualAction(t.NamedTuple):
    context: t.Any
    request: Request
    action: Action

    @property
    def url(self):
        return self.action.resolve(self.request, self.context)

    @property
    def css(self):
        if self.action.attributes:
            return self.action.attributes.get("css", "")
        return ""

    @property
    def title(self):
        return self.action.title

    @property
    def active(self):
        prefix_len = len(self.request.script_name)
        url = self.request.application_uri + self.url[prefix_len:]
        return self.request.uri().startswith(url)

    def __html__(self):
        url = self.url
        if url is None:
            return
        ncss = "nav-link active" if self.active else "nav-link"
        return (
            f'<a class="{ncss}" href="{url}"> '
            f'<i class="{self.css}"> </i>'
            f"{self.action.title}</a>"
        )


class ContextualActions:

    def __init__(self, request: Request, actions: Actions):
        self.request = request
        self.actions = actions

    def get(self, name, context: t.Any = None) -> ContextualAction:
        if context is None:
            context = self.request.app
        action = self.actions.get_action_for(context.__class__, name)
        if action is not None and \
           action.evaluate(context=context, request=self.request) is None:
            return ContextualAction(
                context=context, request=self.request, action=action)

    def iter(self, classifiers: t.Iterable[str] = tuple(),
             context: t.Any = None) -> t.Iterable[ContextualAction]:

        def order(action):
            if action.attributes:
                return action.attributes.get("order", 99)
            return 99

        if context is None:
            context = self.request.app
        if classifiers:
            actions = list(
                self.actions.partial(context.__class__, *classifiers))
        else:
            actions = list(
                self.actions.all_actions_for(context.__class__))
        actions.sort(key=order)
        for action in actions:
            if action.evaluate(context=context, request=self.request) is None:
                yield ContextualAction(
                    context=context, request=self.request, action=action)
