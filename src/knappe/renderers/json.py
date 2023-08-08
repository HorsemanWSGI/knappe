import wrapt
import typing as t
from knappe.response import Response


def json(
        wrapped=None,
        *,
        response_class: t.Type[Response] = Response):
    if wrapped is None:
        return functools.partial(
            json, response_class=Response)

    @wrapt.decorator
    def renderer(wrapped, instance, args, kwargs):
        request = args[0]
        result = wrapped(request, **kwargs)
        if isinstance(result, Response):
            return result
        return response_class.to_json(body=result)
    return renderer(wrapped)
