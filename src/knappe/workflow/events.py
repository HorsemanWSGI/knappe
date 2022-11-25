from typing import Any, Mapping
from knappe.events import Event
from knappe.workflow.components import Transition


class WorkflowTransitionEvent(Event):

    def __init__(self, transition: Transition, obj: Any, namespace: Mapping):
        self.transition = transition
        self.obj = obj
        self.namespace = namespace
