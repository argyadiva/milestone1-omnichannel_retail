"""Stable error types used at the engine boundary."""

from __future__ import annotations


class AnalysisError(RuntimeError):
    """Base class for errors that can be shown as a user-facing analysis failure."""


class ProviderError(AnalysisError):
    """The language-model provider could not produce a query plan."""


class QueryExecutionError(AnalysisError):
    """The generated, validated query could not be executed."""
