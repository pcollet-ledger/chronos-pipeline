"""Registry for workflow task action handlers.

Provides a register/get pattern so that action handlers can be defined
(or overridden) independently of the workflow execution engine.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

ActionHandler = Callable[[Dict[str, Any]], Dict[str, Any]]

_registry: Dict[str, ActionHandler] = {}


def register_action(name: str, handler: ActionHandler) -> None:
    """Register an action handler under *name*, replacing any previous handler."""
    _registry[name] = handler


def get_action(name: str) -> Optional[ActionHandler]:
    """Return the handler registered for *name*, or ``None`` if not found."""
    return _registry.get(name)


def run_action(action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Look up *action* in the registry and execute it with *parameters*.

    Raises ``ValueError`` when no handler is registered for the given action.
    """
    handler = get_action(action)
    if not handler:
        raise ValueError(f"Unknown action: {action}")
    return handler(parameters)


def list_actions() -> list[str]:
    """Return the names of all registered actions."""
    return sorted(_registry)


def clear_actions() -> None:
    """Remove every registered action (useful in tests)."""
    _registry.clear()


# -- Built-in actions --------------------------------------------------------

def _log_action(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"message": p.get("message", "logged")}


def _transform_action(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"transformed": True, "input_keys": list(p.keys())}


def _validate_action(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"valid": bool(p)}


def _notify_action(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"notified": True, "channel": p.get("channel", "default")}


def _aggregate_action(p: Dict[str, Any]) -> Dict[str, Any]:
    return {"count": len(p), "keys": list(p.keys())}


def _register_builtins() -> None:
    """Register the default set of action handlers."""
    register_action("log", _log_action)
    register_action("transform", _transform_action)
    register_action("validate", _validate_action)
    register_action("notify", _notify_action)
    register_action("aggregate", _aggregate_action)


_register_builtins()
