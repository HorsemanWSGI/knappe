import wrapt
from horseman.exceptions import HTTPError


def context(factory, name: str = 'context'):
    @wrapt.decorator
    def context_wrapper(wrapped, instance, args, kwargs):
        if name in kwargs:
            raise NameError(
                f"`context` factory cannot use {name}. "
                "Keyword arguments already contain the key."
            )
        try:
            kwargs[name] = factory(*args, **kwargs)
        except LookupError:
            raise HTTPError(400)
        return wrapped(*args, **kwargs)
    return context_wrapper
