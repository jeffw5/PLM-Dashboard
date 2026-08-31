"""
Component 1 & 2: Atomic Action Blocks + Assembly DAG / Assembly Index.

A Primitive is the smallest reusable, irreversible commitment in any domain
(a capital purchase, a hire, a policy lever, a control). A Strategy/Assembly
is a DAG of Primitives joined by SERIAL, PARALLEL, or CONDITIONAL operators.

The Assembly Index (Ax) follows Assembly Theory's core idea: the number of
join operations needed to build the object, with structurally identical
sub-assemblies reused for free (memoized) rather than rebuilt — i.e. copying
an already-assembled part is cheap, inventing a new joint is not. Ax is used
downstream purely as a complexity regularizer (Occam's razor on strategy
design): more joints -> more coordination surface -> more fragility.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .audit import AuditTrail


@dataclass(frozen=True)
class Primitive:
    """Component 1: Atomic Action Block. Domain supplies the concrete values."""
    id: str
    name: str
    cost: float                 # capital / budget units
    lead_time: float            # periods to bring online
    prior_alpha: float          # Beta prior — "failures"/adverse events
    prior_beta: float           # Beta prior — "successes"
    effects: Dict[str, Any] = field(default_factory=dict)  # domain-specific payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "cost": self.cost,
            "lead_time": self.lead_time,
            "prior_failure_rate": round(self.prior_alpha / (self.prior_alpha + self.prior_beta), 4),
        }


class JoinOp(str, Enum):
    SERIAL = "serial"           # must complete in sequence
    PARALLEL = "parallel"       # independent, concurrent
    CONDITIONAL = "conditional"  # only assembled if a gate condition holds


@dataclass
class AssemblyNode:
    label: str
    primitive: Optional[Primitive] = None
    children: List["AssemblyNode"] = field(default_factory=list)
    join: Optional[JoinOp] = None

    def structural_key(self) -> str:
        if self.primitive is not None:
            return f"P:{self.primitive.id}"
        inner = ",".join(sorted(c.structural_key() for c in self.children))
        return f"{self.join.value}[{inner}]"


class Assembly:
    """Component 2: a compiled candidate Strategy — a DAG of Primitives."""

    def __init__(self, name: str, root: AssemblyNode, audit: Optional[AuditTrail] = None,
                 meta: Optional[Dict[str, Any]] = None):
        self.name = name
        self.root = root
        self._audit = audit
        self.meta = meta or {}  # strategy-level params (e.g. margin multiplier) not tied to one primitive

    def primitives(self) -> List[Primitive]:
        out: List[Primitive] = []
        seen = set()

        def walk(node: AssemblyNode):
            if node.primitive is not None:
                if node.primitive.id not in seen:
                    seen.add(node.primitive.id)
                    out.append(node.primitive)
            for c in node.children:
                walk(c)
        walk(self.root)
        return out

    def total_cost(self) -> float:
        return sum(p.cost for p in self.primitives())

    def critical_path_lead_time(self, node: Optional[AssemblyNode] = None) -> float:
        node = node or self.root
        if node.primitive is not None:
            return node.primitive.lead_time
        child_times = [self.critical_path_lead_time(c) for c in node.children]
        if not child_times:
            return 0.0
        return sum(child_times) if node.join == JoinOp.SERIAL else max(child_times)

    def assembly_index(self) -> int:
        """
        Ax = minimal number of join steps to build this Assembly from
        Primitives, memoizing structurally identical sub-assemblies (they are
        copied for free once built once — the Assembly Theory reuse discount).
        """
        memo: set = set()

        def build_cost(node: AssemblyNode) -> int:
            key = node.structural_key()
            if key in memo:
                return 0  # already assembled elsewhere in the graph — free reuse
            memo.add(key)
            if node.primitive is not None:
                return 0
            steps = sum(build_cost(c) for c in node.children)
            if len(node.children) > 1:
                steps += len(node.children) - 1  # joins needed to combine children
            return steps

        ax = build_cost(self.root)
        if self._audit:
            self._audit.log(
                "Assembly", "assembly_index_computed",
                inputs={"name": self.name, "primitives": [p.id for p in self.primitives()]},
                outputs={"assembly_index": ax, "total_cost": self.total_cost(),
                         "critical_path_lead_time": self.critical_path_lead_time()},
            )
        return ax

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "primitives": [p.to_dict() for p in self.primitives()],
            "assembly_index": self.assembly_index(),
            "total_cost": self.total_cost(),
            "critical_path_lead_time": self.critical_path_lead_time(),
        }


def serial(*nodes: AssemblyNode, label: str = "serial") -> AssemblyNode:
    return AssemblyNode(label=label, children=list(nodes), join=JoinOp.SERIAL)


def parallel(*nodes: AssemblyNode, label: str = "parallel") -> AssemblyNode:
    return AssemblyNode(label=label, children=list(nodes), join=JoinOp.PARALLEL)


def leaf(p: Primitive) -> AssemblyNode:
    return AssemblyNode(label=p.id, primitive=p)
