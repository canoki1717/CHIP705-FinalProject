"""Compare two classifiers using grouped cross-validation by mouse line."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "allen_mouse_spiny_aspiny_analysis.csv"
FIGURE_DIR = PROJECT_DIR / "figures"
RESULT_DIR = PROJECT_DIR / "results"

FEATURES = [
    "ef__vrest",
    "ef__avg_firing_rate",
    "ef__ri",
    "ef__tau",
    "ef__adaptation",
    "ef__avg_isi",
    "ef__f_i_curve_slope",
    "ef__fast_trough_v_long_square",
    "ef__peak_t_ramp",
    "ef__threshold_i_long_square",
    "ef__upstroke_downstroke_ratio_long_square",
]
LABEL_ORDER = ["aspiny", "spiny"]
METRICS = {
    "accuracy": accuracy_score,
    "balanced_accuracy": balanced_accuracy_score,
    "precision_spiny": lambda y, p: precision_score(y, p, zero_division=0),
    "recall_spiny": lambda y, p: recall_score(y, p, zero_division=0),
    "f1_spiny": lambda y, p: f1_score(y, p, zero_division=0),
}


def main() -> None:
    FIGURE_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)
    data = pd.read_csv(DATA_PATH)
    X = data[FEATURES]
    y = data["dendrite_type"].map({"aspiny": 0, "spiny": 1}).astype(int)
    groups = data["line_name"].fillna("unknown_line").astype(str)

    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=705)
    splits = list(cv.split(X, y, groups=groups))
    for fold, (train_idx, test_idx) in enumerate(splits, start=1):
        overlap = set(groups.iloc[train_idx]) & set(groups.iloc[test_idx])
        if overlap:
            raise RuntimeError(f"Mouse-line leakage in fold {fold}: {sorted(overlap)}")
        if y.iloc[test_idx].nunique() < 2:
            raise RuntimeError(f"Fold {fold} contains only one outcome class; revise grouped folds.")

    models = {
        "Logistic Regression": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(max_iter=2000, random_state=705),
        ),
        "Random Forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestClassifier(
                n_estimators=400,
                min_samples_leaf=3,
                class_weight="balanced_subsample",
                random_state=705,
                n_jobs=-1,
            ),
        ),
    }

    metric_rows = []
    fold_rows = []
    prediction_table = data[["specimen_id", "line_name", "dendrite_type"]].copy()
    prediction_table["true_spiny"] = y

    for model_name, model in models.items():
        oof_predictions = np.full(len(data), -1, dtype=int)
        oof_probabilities = np.full(len(data), np.nan, dtype=float)

        for fold, (train_idx, test_idx) in enumerate(splits, start=1):
            model.fit(X.iloc[train_idx], y.iloc[train_idx])
            fold_predictions = model.predict(X.iloc[test_idx])
            fold_probabilities = model.predict_proba(X.iloc[test_idx])[:, 1]
            oof_predictions[test_idx] = fold_predictions
            oof_probabilities[test_idx] = fold_probabilities

            row = {"model": model_name, "fold": fold}
            for metric_name, metric in METRICS.items():
                row[metric_name] = metric(y.iloc[test_idx], fold_predictions)
            row["roc_auc"] = roc_auc_score(y.iloc[test_idx], fold_probabilities)
            row["n_test_cells"] = len(test_idx)
            row["n_test_lines"] = groups.iloc[test_idx].nunique()
            fold_rows.append(row)

        if (oof_predictions < 0).any() or np.isnan(oof_probabilities).any():
            raise RuntimeError(f"Some cells did not receive an out-of-fold prediction for {model_name}.")

        overall = {"model": model_name, "evaluation": "pooled out-of-fold"}
        for metric_name, metric in METRICS.items():
            overall[metric_name] = metric(y, oof_predictions)
        overall["roc_auc"] = roc_auc_score(y, oof_probabilities)
        overall["n_cells"] = len(data)
        metric_rows.append(overall)

        pred_col = "predicted_" + model_name.lower().replace(" ", "_")
        prob_col = "probability_spiny_" + model_name.lower().replace(" ", "_")
        prediction_table[pred_col] = oof_predictions
        prediction_table[prob_col] = oof_probabilities

        matrix = confusion_matrix(y, oof_predictions, labels=[0, 1])
        fig, ax = plt.subplots(figsize=(5.5, 4.5))
        sns.heatmap(
            matrix,
            annot=True,
            fmt="d",
            cmap="crest",
            xticklabels=LABEL_ORDER,
            yticklabels=LABEL_ORDER,
            cbar=False,
            ax=ax,
        )
        ax.set(title=f"{model_name}: grouped cross-validation", xlabel="Predicted label", ylabel="Observed label")
        fig.tight_layout()
        fig.savefig(
            FIGURE_DIR / f"confusion_matrix_{model_name.lower().replace(' ', '_')}.png",
            dpi=220,
        )
        plt.close(fig)

    results = pd.DataFrame(metric_rows)
    fold_results = pd.DataFrame(fold_rows)
    results.to_csv(RESULT_DIR / "model_performance.csv", index=False)
    fold_results.to_csv(RESULT_DIR / "model_performance_by_fold.csv", index=False)
    prediction_table.to_csv(RESULT_DIR / "out_of_fold_predictions.csv", index=False)

    print("Grouped validation: StratifiedGroupKFold, 5 folds, grouped by mouse line")
    print(f"Features: {len(FEATURES)} precomputed electrophysiology variables")
    print(f"Outcome: aspiny=0, spiny=1; total cells={len(data):,}; mouse lines={groups.nunique()}")
    print("Each fold has both classes and no mouse line is shared between its training and test sets.")
    print(results.round(3).to_string(index=False))
    print(f"Saved results in {RESULT_DIR} and confusion matrices in {FIGURE_DIR}.")


if __name__ == "__main__":
    main()
