"""Tabular Feature Engineering and Data Leakage-Free Splitting for Clearance Time.

Extracts, normalizes, and one-hot encodes features for training baseline models
(Linear Regression, Random Forest, XGBoost) and LSTM sequences.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NUMERICAL_FEATURES: list[str] = [
    "queue_length_m",
    "queued_vehicle_count",
    "motorcycle_ratio",
    "heavy_vehicle_count",
    "approach_occupancy",
    "downstream_occupancy",
    "hour_of_day",
]

CATEGORICAL_FEATURES: list[str] = [
    "scenario_id",
    "node_id",
    "approach_id",
    "weather",
]

TARGET_COLUMN = "clearance_time_sec"


class ClearanceFeaturePipeline:
    """Transforms raw clearance dataframes into normalized ML feature matrices."""

    def __init__(self) -> None:
        self.num_means: dict[str, float] = {}
        self.num_stds: dict[str, float] = {}
        self.cat_categories: dict[str, list[str]] = {}
        self.feature_names: list[str] = []
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> ClearanceFeaturePipeline:
        """Learn mean, std, and categorical levels from training split."""
        # Numerical scaling parameters
        for col in NUMERICAL_FEATURES:
            if col in df.columns:
                self.num_means[col] = float(df[col].mean())
                self.num_stds[col] = float(df[col].std()) if df[col].std() > 1e-6 else 1.0

        # Categorical unique categories
        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                self.cat_categories[col] = sorted(df[col].dropna().unique().tolist())

        # Construct feature names
        names: list[str] = list(NUMERICAL_FEATURES)
        for col in CATEGORICAL_FEATURES:
            for cat in self.cat_categories.get(col, []):
                names.append(f"{col}_{cat}")

        self.feature_names = names
        self.is_fitted = True
        return self

    def transform(
        self,
        df: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray | None, list[str]]:
        """Transform dataframe into (X, y, feature_names)."""
        if not self.is_fitted:
            raise RuntimeError("Pipeline must be fit before calling transform.")

        num_arrays: list[np.ndarray] = []
        for col in NUMERICAL_FEATURES:
            vals = df[col].values.astype(float)
            mean = self.num_means.get(col, 0.0)
            std = self.num_stds.get(col, 1.0)
            norm_vals = (vals - mean) / std
            num_arrays.append(norm_vals.reshape(-1, 1))

        cat_arrays: list[np.ndarray] = []
        for col in CATEGORICAL_FEATURES:
            cats = self.cat_categories.get(col, [])
            vals = df[col].values
            for cat in cats:
                encoded = (vals == cat).astype(float).reshape(-1, 1)
                cat_arrays.append(encoded)

        X = np.hstack(num_arrays + cat_arrays)

        y = None
        if TARGET_COLUMN in df.columns:
            y = df[TARGET_COLUMN].values.astype(float)

        return X, y, self.feature_names

    def fit_transform(
        self,
        df: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Fit and transform in one step."""
        self.fit(df)
        X, y, names = self.transform(df)
        assert y is not None
        return X, y, names

    @staticmethod
    def split_by_node(
        df: pd.DataFrame,
        train_nodes: list[str] | None = None,
        val_nodes: list[str] | None = None,
        test_nodes: list[str] | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Disjoint partition by intersection node to prevent spatial-temporal leakage.

        Default partition:
            Train: node_a, node_b (~50%)
            Val:   node_c (~25%)
            Test:  node_d (~25%)
        """
        tr_nodes = train_nodes or ["node_a", "node_b"]
        v_nodes = val_nodes or ["node_c"]
        te_nodes = test_nodes or ["node_d"]

        # Assert zero leakage
        s_tr = set(tr_nodes)
        s_v = set(v_nodes)
        s_te = set(te_nodes)

        assert s_tr.isdisjoint(s_v), f"Train/Val node overlap: {s_tr & s_v}"
        assert s_tr.isdisjoint(s_te), f"Train/Test node overlap: {s_tr & s_te}"
        assert s_v.isdisjoint(s_te), f"Val/Test node overlap: {s_v & s_te}"

        train_df = df[df["node_id"].isin(tr_nodes)].copy()
        val_df = df[df["node_id"].isin(v_nodes)].copy()
        test_df = df[df["node_id"].isin(te_nodes)].copy()

        return train_df, val_df, test_df
