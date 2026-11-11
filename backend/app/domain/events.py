from collections import defaultdict
from typing import Any, Callable
_handlers: dict[str, list] = defaultdict(list)
def subscribe(event_type: str, handler):
    _handlers[event_type].append(handler)
def publish(event_type: str, payload: dict):
    for h in list(_handlers.get(event_type, [])):
        try:
            h(payload)
        except Exception:
            pass
def clear_handlers():
    _handlers.clear()
