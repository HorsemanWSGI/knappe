import typing as t
from abc import ABC, abstractmethod
from knappe.request import Request


Stack = t.Sequence[str]
Context = t.VarType('Context')
Consumer = t.Callable[
    [Stack, t.Any, Request], t.Tuple[Stack, t.Any, Stack]]


class ComponentLookup(ABC):

    @abstractmethod
    def __call__(self, request: Request, obj: t.Any, stack: Stack) -> t.Any:
        """Returns the right object, given the request,
        the context and the stack.
        """


class ContextLookup(ABC, ComponentLookup):

    @abstractmethod
    def register(self, context_type: t.Any, consumer: Consumer):
        """Registers a consumer for the given context_type
        """

    @abstractmethod
    def lookup(self, obj: Context):
        """Get all consumers.
        """

    def __call__(self, request: Request, obj: t.Any, stack: Stack) -> t.Any:
        """Traverses following stack components and starting from obj.
        """
        unconsumed = stack.copy()
        while unconsumed:
            for consumer in self.lookup(obj):
                any_consumed, obj, unconsumed = consumer(
                    request, obj, unconsumed)
                if any_consumed:
                    break
            else:
                # nothing could be consumed
                return obj, unconsumed
        return obj, None
