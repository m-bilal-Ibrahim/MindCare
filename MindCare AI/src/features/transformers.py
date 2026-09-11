"""Custom sklearn-compatible transformers belong here."""

from sklearn.base import BaseEstimator, TransformerMixin


class IdentityTransformer(BaseEstimator, TransformerMixin):
    """A no-op transformer useful as a pipeline placeholder."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X
