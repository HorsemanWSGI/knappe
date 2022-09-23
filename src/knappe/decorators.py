import wrapt
import orjson
from knappe.result import Result


def composed(composer):
    @wrapt.decorator
    def composed(wrapped, instance, args, params):
        result = wrapped(*args, **params)
        if isinstance(result, Result):
            result.layout = composer
        return result
    return composed


def html(template: str, result_class=Result):
    @wrapt.decorator
    def renderer(wrapped, instance, args, params):
        result = wrapped(*args, **params)
        if isinstance(result, Response):
            return result
        request = args[0]
        templates = request.utilities['templates']
        rendered = templates[template].render(**result)
        layout = templates.get('layout')
        return result_class(body=rendered, layout=layout, headers={
            'Content-Type': 'text/html; charset=utf-8'
        })
    return renderer


def json(result_class=Result):
    @wrapt.decorator
    def renderer(wrapped, instance, args, params):
        request = args[0]
        result = wrapped(request, **params)
        if isinstance(result, (Response, Result)):
            return result
        return result_class(body=orjson.dumps(result), headers={
            'Content-Type': 'application/json'
        })
    return renderer


def context(factory):
    @wrapt.decorator
    def context_wrapper(wrapped, instance, args, params):
        try:
            context = factory(*args, **params)
        except LookupError:
            raise HTTPError(400)
        return wrapped(context, *args, **params)
    return context_wrapper
