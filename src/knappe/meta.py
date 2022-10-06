import inspect
import typing as t
from abc import ABCMeta, abstractmethod
from horseman.types import HTTPMethod, HTTPMethods
from knappe.datastructures import EndpointDefinition


METHODS = frozenset(t.get_args(HTTPMethod))


class EndpointType(ABCMeta):

    @abstractmethod
    def as_endpoint(self,
                    metadata: t.Optional[t.Mapping[str, t.Any]] = None,
                    **kwargs) -> EndpointDefinition:
        pass


class HTTPEndpointMeta(EndpointType):

    def as_endpoint(self,
                    methods: t.Optional[HTTPMethods] = None,
                    metadata: t.Optional[t.Mapping[str, t.Any]] = None,
                    **kwargs) -> t.Mapping[HTTPMethod, EndpointDefinition]:

        if methods is None:
            methods = ('GET',)

        inst = self()
        return {
            method: EndpointDefinition(handler=inst, metadata=metadata)
            for method in methods
        }


class HTTPMethodEndpointMeta(HTTPEndpointMeta):

    def as_endpoint(self,
                    methods: t.Optional[HTTPMethods] = None,
                    metadata: t.Optional[t.Mapping[str, t.Any]] = None,
                    **kwargs):

        extract = methods is not None and methods or METHODS
        inst = self()
        available = {
            verb.upper(): EndpointDefinition(
                handler=handler, metadata=metadata
            ) for verb, handler in inspect.getmembers(
                inst, predicate=(lambda x: inspect.ismethod(x)))
            if verb.upper() in extract
        }
        if methods is not None:
            if unknown := (set(methods) - set(available.keys())):
                raise ValueError(
                    f"Missing HTTP method(s): {', '.join(unknown)}")

        return available
