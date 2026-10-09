"""
Components: Primitive and Assembly — Assembly Theory's atomic action block
and the DAG of primitives that forms a strategy (or, in the World Model,
an institutional decision). Assembly Index (Ax) counts join operations
net of structural reuse: a complexity regularizer, not a cost estimate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .audit import AuditTrail


@dataclass(frozen=True)
class Primitive:
    id: str
    name: str
    cost: float
    lead_time: int
    prior_failure_rate: float = 0.0
    tags: tuple = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "cost": self.cost,
            "lead_time": self.lead_time, "prior_failure_rate": self.prior_failure_rate,
            "tags": list(self.tags),
        }


class Assembly:
    """
    A specific combination of primitives, joined into a build-order DAG.
    For the simple chain-style assemblies used across these domains, the
    Assembly Index is computed by counting join operations needed to
    combine N primitives (N-1 joins for a flat combination), minus any
    discount for substructures explicitly marked as reused.
    """

    def __init__(self, name: str, primitive_list: List[Primitive],
                 audit: Optional[AuditTrail] = None, reused_subassemblies: int = 0):
        self.name = name
        self._primitives = list(primitive_list)
        self._reused = reused_subassemblies
        self.audit = audit
        if audit:
            audit.log("Assembly", "constructed",
                       inputs={"name": name, "primitive_ids": [p.id for p in primitive_list],
                               "reused_subassemblies": reused_subassemblies},
                       outputs={"assembly_index": self.assembly_index, "total_cost": self.total_cost,
                                "critical_path_lead_time": self.critical_path_lead_time})

    def primitives(self) -> List[Primitive]:
        return self._primitives

    @property
    def assembly_index(self) -> int:
        n = len(self._primitives)
        if n <= 1:
            return 0
        return max(0, (n - 1) - self._reused)

    @property
    def total_cost(self) -> float:
        return round(sum(p.cost for p in self._primitives), 3)

    @property
    def critical_path_lead_time(self) -> int:
        return max((p.lead_time for p in self._primitives), default=0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "primitives": [p.to_dict() for p in self._primitives],
            "assembly_index": self.assembly_index,
            "total_cost": self.total_cost,
            "critical_path_lead_time": self.critical_path_lead_time,
        }
