"""
AuditTrail — full traceability & auditability for every component call.

Every component in this engine (Primitive instantiation, Assembly compilation,
Bayesian updates, Monte Carlo runs, state transitions, risk evaluation) writes
a structured, hashed event into an AuditTrail instead of just returning a
number. This gives:

  - Traceability: every output can be walked back to the exact inputs,
    random seed, and component version that produced it.
  - Auditability: events are content-hashed (sha256 of a canonical JSON
    encoding) so a downstream consumer can verify nothing was altered,
    and the whole run can be replayed deterministically from its seed.
  - Explainability substrate: the Explainer (explain.py) reads the trail
    to build human-readable rationale instead of re-deriving it.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _hash(obj: Any) -> str:
    try:
        payload = json.dumps(obj, sort_keys=True, default=str)
    except TypeError:
        payload = str(obj)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass
class AuditEvent:
    id: str
    ts: float
    component: str          # e.g. "Assembly", "BayesianBeliefNode", "MonteCarloEngine"
    event: str               # e.g. "assembly_index_computed", "posterior_update"
    parent_id: Optional[str]
    domain: Optional[str]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    inputs_hash: str
    outputs_hash: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.ts,
            "component": self.component,
            "event": self.event,
            "parent_id": self.parent_id,
            "domain": self.domain,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "inputs_hash": self.inputs_hash,
            "outputs_hash": self.outputs_hash,
            "meta": self.meta,
        }


class AuditTrail:
    """Ordered, queryable, hashable log of every decision-engine event."""

    def __init__(self, domain: str):
        self.domain = domain
        self.events: List[AuditEvent] = []
        self._span_stack: List[str] = []

    def log(self, component: str, event: str, inputs: Dict[str, Any],
            outputs: Dict[str, Any], **meta) -> str:
        eid = uuid.uuid4().hex[:12]
        parent = self._span_stack[-1] if self._span_stack else None
        rec = AuditEvent(
            id=eid, ts=time.time(), component=component, event=event,
            parent_id=parent, domain=self.domain,
            inputs=inputs, outputs=outputs,
            inputs_hash=_hash(inputs), outputs_hash=_hash(outputs),
            meta=meta,
        )
        self.events.append(rec)
        return eid

    @contextmanager
    def span(self, component: str, event: str, **meta):
        """Group child events under one parent span, e.g. one strategy's MC run."""
        eid = uuid.uuid4().hex[:12]
        parent = self._span_stack[-1] if self._span_stack else None
        rec = AuditEvent(
            id=eid, ts=time.time(), component=component, event=event,
            parent_id=parent, domain=self.domain,
            inputs=meta.get("inputs", {}), outputs={},
            inputs_hash=_hash(meta.get("inputs", {})), outputs_hash="",
            meta={k: v for k, v in meta.items() if k != "inputs"},
        )
        self.events.append(rec)
        self._span_stack.append(eid)
        try:
            yield eid
        finally:
            self._span_stack.pop()

    def children(self, event_id: str) -> List[AuditEvent]:
        return [e for e in self.events if e.parent_id == event_id]

    def chain_hash(self) -> str:
        """A single hash over the whole ordered trail — tamper-evidence for the run."""
        return _hash([e.inputs_hash + e.outputs_hash for e in self.events])

    def to_json(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.events]

    def summary(self) -> Dict[str, Any]:
        by_component: Dict[str, int] = {}
        for e in self.events:
            by_component[e.component] = by_component.get(e.component, 0) + 1
        return {
            "domain": self.domain,
            "n_events": len(self.events),
            "by_component": by_component,
            "chain_hash": self.chain_hash(),
        }
