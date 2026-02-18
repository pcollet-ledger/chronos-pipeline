"""Registry for workflow task action handlers.

Provides a register/get pattern so that action handlers can be defined
independently of the workflow engine and extended without modifying
engine internals.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

ActionHandler = Callable[[Dict[str, Any]], Dict[str, Any]]

_registry: Dict[str, ActionHandler] = {}


def register_action(name: str, handler: ActionHandler) -> None:
    """Register an action handler under *name*.

    Raises ``ValueError`` if *name* is already registered.
    """
    if name in _registry:
        raise ValueError(f"Action already registered: {name}")
    _registry[name] = handler


def get_action(name: str) -> Optional[ActionHandler]:
    """Return the handler for *name*, or ``None`` if not registered."""
    return _registry.get(name)


def run_action(action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Look up *action* in the registry and execute it with *parameters*.

    Raises ``ValueError`` when the action is unknown.
    """
    handler = get_action(action)
    if not handler:
        raise ValueError(f"Unknown action: {action}")
    return handler(parameters)


def registered_actions() -> list[str]:
    """Return a sorted list of all registered action names."""
    return sorted(_registry)


def clear_registry() -> None:
    """Remove all registered actions (useful for testing)."""
    _registry.clear()


# -- Built-in actions --------------------------------------------------------

def _log(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"message": params.get("message", "logged")}


def _transform(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"transformed": True, "input_keys": list(params.keys())}


def _validate(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"valid": bool(params)}


def _notify(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"notified": True, "channel": params.get("channel", "default")}


def _aggregate(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"count": len(params), "keys": list(params.keys())}


def _register_builtins() -> None:
    """Register the default set of built-in action handlers."""
    builtins: Dict[str, ActionHandler] = {
        "log": _log,
        "transform": _transform,
        "validate": _validate,
        "notify": _notify,
        "aggregate": _aggregate,
    }
    for name, handler in builtins.items():
        if name not in _registry:
            register_action(name, handler)


_register_builtins()
