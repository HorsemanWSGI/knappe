import wrapt
from horseman.exceptions import HTTPError


def context(factory):
    @wrapt.decorator
    def context_wrapper(wrapped, instance, args, kwargs):
        try:
            context = factory(*args, **kwargs)
        except LookupError:
            raise HTTPError(400)
        return wrapped(*args, context, **kwargs)
    return context_wrapper
