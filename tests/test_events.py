import pytest
from unittest.mock import Mock
from knappe.events import Event, Subscribers, Subscription
from prejudice.errors import ConstraintError
from prejudice.validators import Or


class ObjectCreatedEvent(Event):

    def __init__(self, request, obj):
        self.request = request
        self.obj = obj


class NonEvent:  # won't be picked up by lineage
    pass


class UserCreatedEvent(NonEvent, ObjectCreatedEvent):
    pass


def test_instanciation():
    subscribers = Subscribers()
    assert subscribers.strict is False
    assert subscribers == {}

    subscribers = Subscribers(strict=True)
    assert subscribers.strict is True
    assert subscribers == {}


def test_registration():
    tracker = Mock()
    subscribers = Subscribers()

    @subscribers.subscribe(ObjectCreatedEvent)
    def my_subscriber(event: ObjectCreatedEvent):
        tracker(event)

    event = ObjectCreatedEvent(1, 2)
    subscribers.notify(event)
    tracker.assert_called_once_with(event)

    assert ObjectCreatedEvent in subscribers
    assert UserCreatedEvent not in subscribers
    assert len(subscribers) == 1
    assert subscribers.get(ObjectCreatedEvent) == [
        Subscription(my_subscriber)
    ]
    assert subscribers.get(UserCreatedEvent) is None


def test_registration_with_predicates():

    tracker = Mock()
    subscribers = Subscribers()

    def Type(*allowed_types):
        def type_checker(event):
            if not isinstance(event.obj, allowed_types):
                raise ConstraintError(
                    f'Expected object of type: {allowed_types}'
                )
        return type_checker

    @subscribers.subscribe(ObjectCreatedEvent, Type(str))
    def my_subscriber(event: ObjectCreatedEvent):
        tracker(event)

    event = ObjectCreatedEvent(1, 2)
    subscribers.notify(event)
    tracker.assert_not_called()

    event2 = ObjectCreatedEvent(1, '2')
    subscribers.notify(event2)
    tracker.assert_called_once_with(event2)

    assert ObjectCreatedEvent in subscribers
    assert UserCreatedEvent not in subscribers
    assert len(subscribers) == 1
    assert subscribers.get(UserCreatedEvent) is None


def test_registration_with_multiple_predicates():

    tracker = Mock()
    subscribers = Subscribers()

    def Type(*allowed_types):
        def type_checker(event):
            if not isinstance(event.obj, allowed_types):
                raise ConstraintError(
                    f'Expected object of type: {allowed_types}'
                )
        return type_checker

    def ObjectValue(*allowed_values):
        def value_checker(event):
            if event.obj not in allowed_values:
                raise ConstraintError(
                    f'Expected object of value: {allowed_values}'
                )
        return value_checker

    @subscribers.subscribe(ObjectCreatedEvent, Type(str), ObjectValue('3'))
    def my_subscriber(event: ObjectCreatedEvent):
        tracker(event)

    event = ObjectCreatedEvent(1, 2)
    subscribers.notify(event)
    tracker.assert_not_called()

    event2 = ObjectCreatedEvent(1, '2')
    subscribers.notify(event2)
    tracker.assert_not_called()

    event3 = ObjectCreatedEvent(1, '3')
    subscribers.notify(event3)
    tracker.assert_called_once_with(event3)


def test_registration_with_OR_predicates():

    tracker = Mock()
    subscribers = Subscribers()

    def Type(*allowed_types):
        def type_checker(event):
            if not isinstance(event.obj, allowed_types):
                raise ConstraintError(
                    f'Expected object of type: {allowed_types}'
                )
        return type_checker

    def ObjectValue(*allowed_values):
        def value_checker(event):
            if event.obj not in allowed_values:
                raise ConstraintError(
                    f'Expected object of value: {allowed_values}'
                )
        return value_checker

    @subscribers.subscribe(
        ObjectCreatedEvent, Or((Type(int), ObjectValue('3'))))
    def my_subscriber(event: ObjectCreatedEvent):
        tracker(event)

    event = ObjectCreatedEvent(1, 2)
    subscribers.notify(event)
    tracker.assert_called_once_with(event)
    tracker.reset_mock()

    event2 = ObjectCreatedEvent(1, '3')
    subscribers.notify(event2)
    tracker.assert_called_once_with(event2)
    tracker.reset_mock()

    event3 = ObjectCreatedEvent(1, '42')
    subscribers.notify(event3)
    tracker.assert_not_called()


def test_subscriber_add_remove():
    subscribers = Subscribers()

    def my_subscriber(event: ObjectCreatedEvent):
        pass

    subscribers.add_subscriber(ObjectCreatedEvent, my_subscriber)
    subscribers.remove(ObjectCreatedEvent, my_subscriber)
    assert list(subscribers.get(ObjectCreatedEvent)) == []

    # wrong key
    subscribers.add_subscriber(ObjectCreatedEvent, my_subscriber)
    with pytest.raises(KeyError):
        subscribers.remove(UserCreatedEvent, my_subscriber)

    with pytest.raises(ValueError):
        subscribers.remove(ObjectCreatedEvent, 'test')


def test_registration_lineage_annotation():
    subscribers = Subscribers()

    @subscribers.subscribe(UserCreatedEvent)
    def my_subscriber(event: ObjectCreatedEvent):
        pass

    assert list(subscribers.get(UserCreatedEvent)) == [
        Subscription(my_subscriber)
    ]


def test_wrong_registration():
    subscribers = Subscribers(strict=True)

    with pytest.raises(KeyError) as exc:
        @subscribers.subscribe(NonEvent)
        def my_subscriber(event):  # noqa: F811
            pass
    assert str(exc.value) == "'Subscriber must be a subclass of Event'"

    with pytest.raises(TypeError) as exc:
        @subscribers.subscribe(ObjectCreatedEvent)
        def my_subscriber(request, event):  # noqa: F811
            pass
    assert str(exc.value) == "A subscriber function takes only 1 argument"

    with pytest.raises(TypeError) as exc:
        @subscribers.subscribe(ObjectCreatedEvent)
        def my_subscriber(event: UserCreatedEvent):  # noqa: F811
            pass
    assert str(exc.value) == (
        "Argument 'event' should hint "
        "<class 'test_events.ObjectCreatedEvent'> "
        "and not <class 'test_events.UserCreatedEvent'>."
    )

    with pytest.raises(ValueError) as exc:
        subscribers.add_subscriber(ObjectCreatedEvent, 'an str')
    assert str(exc.value) == (
        "Subscriber must be a "
        "typing.Callable[[knappe.events.Event], typing.Any]"
    )


def test_nonstrict_registration():

    subscribers = Subscribers()
    subscribers.strict = False

    @subscribers.subscribe(NonEvent)
    def my_subscriber(event):
        pass

    assert list(subscribers.get(NonEvent)) == [
        Subscription(my_subscriber)
    ]


def test_lineage_propagation():
    tracker = []
    subscribers = Subscribers()

    @subscribers.subscribe(ObjectCreatedEvent)
    def my_subscriber(event: ObjectCreatedEvent):
        tracker.append(2)

    @subscribers.subscribe(UserCreatedEvent)
    def user_was_added(event: UserCreatedEvent):
        tracker.append(1)

    assert len(subscribers) == 2
    event = UserCreatedEvent(1, 2)
    subscribers.notify(event)
    assert tracker == [1, 2]


def test_a_result_stops_iteration():
    tracker = []
    subscribers = Subscribers()

    @subscribers.subscribe(ObjectCreatedEvent)
    def my_subscriber(event: ObjectCreatedEvent):
        tracker.append('it happened')

    @subscribers.subscribe(UserCreatedEvent)
    def user_was_added(event: UserCreatedEvent):
        return 'stop'

    assert len(subscribers) == 2
    event = UserCreatedEvent(1, 2)
    assert subscribers.notify(event) == 'stop'
    assert tracker == []


def test_subscribers_methods():
    subscribers = Subscribers()

    @subscribers.subscribe(ObjectCreatedEvent)
    def my_subscriber(event: ObjectCreatedEvent):
        pass

    @subscribers.subscribe(ObjectCreatedEvent)
    def other_subscriber(event: ObjectCreatedEvent):
        pass

    @subscribers.subscribe(UserCreatedEvent)
    def user_was_added(event: UserCreatedEvent):
        pass

    assert len(subscribers) == 2
    assert list(subscribers.items()) == [
        (ObjectCreatedEvent, [
            Subscription(my_subscriber),
            Subscription(other_subscriber)
        ]),
        (UserCreatedEvent, [
            Subscription(user_was_added),
        ]),
    ]
