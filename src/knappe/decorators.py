import wrapt
import orjson
import functools
from knappe.response import Response, BaseResponse


@wrapt.decorator
def composed(wrapped, instance, args, params):
    result = wrapped(*args, **params)
    if isinstance(result, Response):
        result.layout = None
    return result


def html(template_name: str, response_class=Response, default_template=None):
    @wrapt.decorator
    def renderer(wrapped, instance, args, params):
        result = wrapped(*args, **params)
        if isinstance(result, BaseResponse):
            return result
        request = args[0]
        ui = request.utilities['ui']
        template = ui.templates.get(template_name, default_template)
        if template is None:
            raise NotImplementedError('No template.')
        rendered = template.render(**result)
        response = response_class(body=rendered, layout=ui.layout, headers={
            'Content-Type': 'text/html; charset=utf-8'
        })
        response.bind(request)
        return response
    return renderer


def json(wrapped=None, *, response_class=Response):
    if wrapped is None:
        return functools.partial(
            json, response_class=Response)

    @wrapt.decorator
    def renderer(wrapped, instance, args, params):
        request = args[0]
        result = wrapped(request, **params)
        if isinstance(result, Response):
            return result
        response = response_class(body=orjson.dumps(result), headers={
            'Content-Type': 'application/json'
        })
        response.bind(request)
        return response
    return renderer(wrapped)


def context(factory):
    @wrapt.decorator
    def context_wrapper(wrapped, instance, args, params):
        try:
            context = factory(*args, **params)
        except LookupError:
            raise HTTPError(400)
        return wrapped(context, *args, **params)
    return context_wrapper
