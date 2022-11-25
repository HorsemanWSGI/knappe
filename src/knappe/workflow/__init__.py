import enum
import typing as t
from knappe.events import Subscribers
from knappe.workflow.events import WorkflowTransitionEvent
from knappe.workflow.components import (
    Action, State, Stateful, Transition, Transitions
)


class WorkflowState(State, enum.Enum):
    pass


class WorkflowContext:

    def __init__(self,
                 workflow: 'Workflow',
                 item: Stateful,
                 namespace: t.Mapping[str, t.Any]):
        self.workflow = workflow
        self.item = item
        self.namespace = namespace

    @property
    def state(self) -> WorkflowState:
        return self.workflow.get(self.item.state)

    @state.setter
    def state(self, wfstate: WorkflowState):
        self.item.state = self.workflow.states(wfstate).name

    def get_possible_transitions(self):
        return tuple(self.workflow.transitions.available(
             self.state, self.item, **self.namespace))

    def get_transition(self, target: State) -> t.Optional[Transition]:
        target = self.workflow.states(target)  # idempotent
        return self.workflow.transitions.find(self.state, target)

    def apply_transition(self, transition: Transition):
        error = transition.action.check_constraints(
            self.item, **self.namespace)
        if error is not None:
            raise error
        self.state = transition.target
        self.workflow.subscribers.notify(
            WorkflowTransitionEvent(
                transition, self.item, self.namespace)
        )

    def transition_to(self, state: State):
        transition = self.get_transition(state)
        self.apply_transition(transition)


class Workflow:

    context: t.ClassVar[t.Type[WorkflowContext]] = WorkflowContext
    states: t.ClassVar[t.Type[WorkflowState]]
    transitions: t.ClassVar[Transitions]

    default_state: WorkflowState
    subscribers: Subscribers

    def __init__(self, default_state: t.Union[WorkflowState, str]):
        if isinstance(default_state, WorkflowState):
            self.default_state = self.states(default_state)
        elif isinstance(default_state, str):
            self.default_state = self.states[default_state]
        else:
            raise TypeError(
                f'`default_state` of wrong type: {type(default_state)}')
        self.subscribers = Subscribers()

    def __getitem__(self, name: str) -> WorkflowState:
        return self.states[name]

    def __call__(self, item: Stateful, **namespace) -> WorkflowContext:
        return self.context(self, item, namespace)

    def get(self, name=None):
        if name is None:
            return self.default_state
        return self.states[name]


class StateProperty:

    def __init__(self, workflow: Workflow):
        self.workflow = workflow

    def __set__(self, inst, state: t.Union[WorkflowState, str]):
        if isinstance(state, str):
            state = self.workflow.states(state)
        wf = self.workflow(inst)
        wf.transition_to(state)

    def __get__(self, inst, klass):
        if inst is None:
            return self
        return self.workflow(inst).state


__all__ = [
    "Action",
    "State",
    "StateProperty",
    "Stateful",
    "Transition",
    "Transitions",
    "Workflow",
    "WorkflowContext",
    "WorkflowState",
]
