import typing as t
from inspect import unwrap, getmembers, isroutine


class annotation:

    name: t.ClassVar[str] = "__annotations__"

    def __init__(self, **values):
        self.annotation = values

    @staticmethod
    def discriminator(component) -> t.Optional[Exception]:
        if not isroutine(component):
            return TypeError(f"{component!r} is not a routine.")
        if component.__name__.startswith("_"):
            return NameError(f"{component!r} has a private name.")
        return None

    @classmethod
    def predicate(cls, component):
        if cls.discriminator(component) is not None:
            return False
        return True

    def __call__(self, func):
        canonical = unwrap(func)
        if error := self.discriminator(canonical):
            raise error
        setattr(canonical, self.name, self.annotation)
        return func

    @classmethod
    def find(cls, obj_or_module):
        members = getmembers(obj_or_module, predicate=cls.predicate)
        for name, func in members:
            canonical = unwrap(func)
            if annotations := getattr(canonical, cls.name, False):
                yield annotations, func


class annotation_mapping(annotation):

    container: t.ClassVar[t.Type[t.MutableMapping]] = dict

    def __init__(self, key: str, **values):
        self.key = key
        self.annotation = values

    def __call__(self, func):
        canonical = unwrap(func)
        if error := self.discriminator(canonical):
            raise error
        if (annotations := getattr(canonical, self.name, None)) is not None:
            if not isinstance(annotations, self.container):
                raise TypeError('Unknown type of annotations container.')
        else:
            annotations = self.container()
            setattr(canonical, self.name, annotations)

        annotations = self.annotation
        return func
