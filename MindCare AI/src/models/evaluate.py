"""Evaluation helpers."""

from sklearn.metrics import accuracy_score


def classification_accuracy(actual, predicted) -> float:
    """Return classification accuracy as a float."""
    return float(accuracy_score(actual, predicted))
