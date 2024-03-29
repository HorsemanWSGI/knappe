import inspect
import typing as t
from pathlib import Path
from types import MappingProxyType
from chameleon.zpt import template
from pkg_resources import resource_filename
from knappe.collections import PriorityChain


EXPRESSION_TYPES: t.Mapping[str, t.Callable[[str], t.Callable]] = {}


def scan_templates(path: Path, allowed_suffixes=(".pt", ".cpt")):
    for child in path.iterdir():
        if child.is_dir():
            yield from scan_templates(child, allowed_suffixes)
        elif child.is_file() and child.suffix in allowed_suffixes:
            yield child


class Templates(t.Mapping[str, template.PageTemplate]):

    registry: t.MutableMapping[str, Path]
    cache: t.MutableMapping[str, template.PageTemplate]
    extensions = {
        ".pt": template.PageTemplateFile,
        ".cpt": template.PageTemplateFile,
        ".txt": template.PageTextTemplateFile,
    }
    expression_types = MappingProxyType(EXPRESSION_TYPES)

    def __init__(self, prefix: str | None = None):
        self.registry = {}
        self.cache = {}
        self.prefix = prefix

    def register_package_resources(self, pkgpath: str):
        pkg, resource_name = pkgpath.split(":", 1)
        path = resource_filename(pkg, resource_name)
        self.register_path(path)
        return self  # for chaining

    def register_path(self, path: Path | str):
        path = Path(path)  # idempotent
        if not path.is_absolute():
            callerframerecord = inspect.stack()[1]
            frame = callerframerecord[0]
            info = inspect.getframeinfo(frame)
            path = Path(info.filename).parent / path

        for tpl in scan_templates(path, tuple(self.extensions.keys())):
            name = str(tpl.relative_to(path).with_suffix('').as_posix())
            if conflict := self.registry.get(name):
                raise KeyError(
                    f'{name!r} exists: {tpl!r} overrides {conflict!r}.')
            self.registry[f'{self.prefix or ""}{name}'] = tpl
        return self  # for chaining

    def __iter__(self):
        return iter(self.registry)

    def __len__(self):
        return len(self.registry)

    def __lt__(self, other: 'Templates'):
        return tuple(self.keys()) < tuple(self.keys())

    def macro(self, name: str, macroname: str):
        return self[name].macros[macroname]

    def __getitem__(self, name):
        if tpl := self.cache.get(name):
            return tpl

        if path := self.registry.get(name):
            factory = self.extensions[path.suffix]
            tpl = self.cache[name] = factory(path)
            tpl.expression_types |= self.expression_types
            return tpl

        raise KeyError(f"Template not found: {name}.")

    def __or__(self, reg: 'Templates'):
        if not isinstance(reg, Templates):
            raise TypeError(
                f'Cannot merge {self.__class__!r} with {reg.__class__!r}.')
        templates = self.__class__()
        templates.registry = self.registry | reg.registry
        # ensure cache consistency. Merged cache should have precedence on merged overriding templates
        templates.cache = {p: t for p, t in self.cache.items() if p not in reg.registry} | reg.cache
        return templates

    def __ior__(self, reg: 'Templates'):
        return self | reg


class TemplatesChain(PriorityChain[t.Tuple[int, Templates]]):

    def register(self, registry: Templates, order: int = 0):
        return self.add((order, registry))
    def get(self, name):
        for order, reg in self._chain:
            try:
               tpl = reg[name]
               return tpl
            except KeyError:
                continue
        return None
