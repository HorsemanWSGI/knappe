import typing as t
from kavallerie.request import Request
from horseman.response import Response, BODYLESS


class Result(Response):

    namespace: t.Mapping[str, t.Any]
    layout: t.Optional[t.Callable[[str], str]]
    request: t.Optional[Request]

    def __init__(self, *args,
                 layout=None, namespace=None, request=None, **kwargs):
        self.layout = layout
        self.namespace = namespace or {}
        self.request = request
        super().__init__(*args, **kwargs)

    @property
    def content_type(self):
        return self.headers.get('Content-Type')

    @content_type.setter
    def content_type(self, ctype):
        self.headers['Content-Type'] = ctype

    def render(self):
        if self.layout is not None \
           and self.layout.accepts(self.content_type):
            return self.layout(self.body, **self.metadata)
        return self.body

    def __iter__(self):
        if self.status not in BODYLESS:
            if self.body is None:
                yield self.status.description.encode()
                return

            body = self.render()
            if isinstance(body, bytes):
                yield body
            elif isinstance(body, str):
                yield body.encode()
            elif isinstance(body, (t.Generator, t.Iterable)):
                yield from body
            else:
                raise TypeError(
                    f'Body of type {type(self.body)!r} is not supported.'
                )
