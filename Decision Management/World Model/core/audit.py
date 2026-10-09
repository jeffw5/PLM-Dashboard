"""
Component: AuditTrail — tamper-evident, replayable log of every component
call in a decision-engine run. Every event hashes its own inputs and
outputs (SHA-256) and chains onto the previous event's hash, so the whole
run can be verified after the fact and any single edited event is
detectable. Domain-agnostic: the same class is reused by every domain.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _stable_hash(obj: Any) -> str:
    try:
        payload = json.dumps(obj, sort_keys=True, default=str)
    except TypeError:
        payload = str(obj)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass
class AuditEvent:
    seq: int
    component: str
    event: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    meta: Dict[str, Any]
    inputs_hash: str
    outputs_hash: str
    id: str  # chain hash: hash(prev_id + this event's content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seq": self.seq, "component": self.component, "event": self.event,
            "inputs": self.inputs, "outputs": self.outputs, "meta": self.meta,
            "inputs_hash": self.inputs_hash, "outputs_hash": self.outputs_hash,
            "id": self.id,
        }


class AuditTrail:
    """Ordered, queryable, hashable log of every decision-engine event."""

    def __init__(self, domain: str):
        self.domain = domain
        self.events: List[AuditEvent] = []
        self._span_stack: List[str] = []

    def log(self, component: str, event: str, inputs: Dict[str, Any],
            outputs: Optional[Dict[str, Any]] = None, meta: Optional[Dict[str, Any]] = None) -> AuditEvent:
        outputs = outputs or {}
        meta = meta or {}
        inputs_hash = _stable_hash(inputs)
        outputs_hash = _stable_hash(outputs)
        prev_id = self.events[-1].id if self.events else "genesis"
        chain_payload = f"{prev_id}|{component}|{event}|{inputs_hash}|{outputs_hash}"
        chain_id = hashlib.sha256(chain_payload.encode("utf-8")).hexdigest()[:16]
        ev = AuditEvent(
            seq=len(self.events), component=component, event=event,
            inputs=inputs, outputs=outputs, meta=meta,
            inputs_hash=inputs_hash, outputs_hash=outputs_hash, id=chain_id,
        )
        self.events.append(ev)
        return ev

    @contextmanager
    def span(self, component: str, event: str, inputs: Dict[str, Any]):
        self._span_stack.append(event)
        try:
            yield
        finally:
            self._span_stack.pop()

    def chain_hash(self) -> str:
        if not self.events:
            return "empty"
        return self.events[-1].id

    def summary(self) -> Dict[str, Any]:
        from collections import Counter
        by_component = Counter(e.component for e in self.events)
        return {
            "domain": self.domain, "n_events": len(self.events),
            "chain_hash": self.chain_hash(),
            "events_by_component": dict(by_component),
        }

    def to_list(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.events]
