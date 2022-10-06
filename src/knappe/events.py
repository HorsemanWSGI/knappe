from knappe.collections import TypeMapping
import abc
import collections.abc
import typing as t
from inspect import isclass, signature
from prejudice.types import Predicate, Predicates
from prejudice.utils import resolve_constraints


class Event(abc.ABC):

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        """This needs to be overridden in subclasses.
        """

    def __repr__(self):
        return f"<Event({self.__class__!r})>"


Subscriber = t.Callable[[Event], t.Any]


class Subscription(t.NamedTuple):
    subscriber: Subscriber
    predicates: t.Optional[Predicates] = None

    def check(self, event: Event) -> bool:
        if self.predicates:
            return resolve_constraints(self.predicates, event)
        return None

    def __call__(self, event: Event, silence=True) -> t.Any:
        error = self.check(event)
        if error is None:
            return self.subscriber(event)
        elif not silence:
            raise error


class Subscribers(TypeMapping[Event, Subscription]):

    __slots__ = ('strict',)

    def __init__(self, strict: bool = False):
        self.strict = strict

    @staticmethod
    def lineage(cls: t.Type[Event]):
        for parent in cls.__mro__:
            if parent is Event:
                break
            if issubclass(parent, Event):
                yield parent

    def remove(self,
               event_type: t.Type[Event],
               subscriber: Subscriber):
        subscribers = self.get(event_type)
        if not subscribers:
            raise KeyError(f"{event_type} has no subscribers.")

        removed = 0
        for subscription in subscribers:
            if subscription.subscriber is subscriber:
                subscribers.remove(subscription)
                removed += 1
        if not removed:
            raise ValueError(
                f"{event_type} has no subscription for {subscriber}.")

    def add_subscriber(self,
                      event_type: t.Type[Event],
                      subscriber: Subscriber,
                      *predicates: Predicate):
        if self.strict:
            self.check_subscriber(event_type, subscriber)
        if not predicates:
            predicates = None
        subscription = Subscription(
            subscriber=subscriber,
            predicates=predicates
        )
        self.add(event_type, subscription)

    def subscribe(self,
                  event_type: t.Type[Event],
                  *predicates: Predicate):
        def register_subscriber(subscriber: Subscriber) -> Subscriber:
            self.add_subscriber(event_type, subscriber, *predicates)
            return subscriber

        return register_subscriber

    def notify(self, event: Event) -> t.Any:
        for sub in self.lookup(event.__class__):
            result = sub(event)
            if result is not None:  # Allow breaking.
                return result

    @staticmethod
    def check_subscriber(event_type: t.Type[Event], sub: Subscriber):
        if not (isclass(event_type) and issubclass(event_type, Event)):
            raise KeyError('Subscriber must be a subclass of Event')
        if not isinstance(sub, t.Callable):
            raise ValueError(f'Subscriber must be a {Subscriber}')
        sig = signature(sub)
        if len(sig.parameters) != 1:
            raise TypeError('A subscriber function takes only 1 argument')
        param = list(sig.parameters.values())[0]
        if param.annotation is not param.empty and \
           not issubclass(event_type, param.annotation):
            raise TypeError(
                f'Argument {param.name!r} should hint {event_type!r} '
                f'and not {param.annotation!r}.'
            )
