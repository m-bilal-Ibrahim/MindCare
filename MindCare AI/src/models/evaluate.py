"""Classification evaluation helpers."""

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def classification_accuracy(actual, predicted) -> float:
    """Return classification accuracy as a float."""
    return float(accuracy_score(actual, predicted))


def classification_metrics(actual, predicted) -> dict[str, float]:
    """Return metrics that account for imbalanced severity classes."""
    return {
        "accuracy": classification_accuracy(actual, predicted),
        "macro_precision": float(precision_score(actual, predicted, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(actual, predicted, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(actual, predicted, average="macro", zero_division=0)),
    }
