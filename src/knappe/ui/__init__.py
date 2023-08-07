import typing as t
from dataclasses import dataclass, field
from knappe.components.meta import NamedRegistry
from .templates import Templates


@dataclass
class UI:
    slots: NamedRegistry = field(default_factory=NamedRegistry)
    layouts: NamedRegistry = field(default_factory=NamedRegistry)
    templates: Templates = field(default_factory=Templates)
    macros: Templates = field(default_factory=Templates)
    resources: t.Set = field(default_factory=set)
