"""Facade of the simple-build tool: the contract API re-exported by identity."""

from .registration import build_presets, register_hooks

__all__ = ["build_presets", "register_hooks"]
