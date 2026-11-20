"""Create the first descriptive summary and plots for the neuron project."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "allen_mouse_spiny_aspiny_analysis.csv"
FIGURE_DIR = PROJECT_DIR / "figures"
RESULT_DIR = PROJECT_DIR / "results"

FEATURES = {
    "ef__vrest": "Resting potential (mV)",
    "ef__avg_firing_rate": "Average firing rate (spikes/s)",
    "ef__ri": "Input resistance (MΩ)",
    "ef__tau": "Membrane time constant (ms)",
    "ef__adaptation": "Adaptation index",
    "ef__avg_isi": "Average interspike interval (ms)",
    "ef__f_i_curve_slope": "F-I curve slope (spikes/s/pA)",
    "ef__fast_trough_v_long_square": "Fast AP trough (mV)",
    "ef__peak_t_ramp": "Ramp spike time (s)",
    "ef__threshold_i_long_square": "Threshold current (pA)",
    "ef__upstroke_downstroke_ratio_long_square": "Upstroke/downstroke ratio",
}


def main() -> None:
    FIGURE_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)
    data = pd.read_csv(DATA_PATH)

    missing_features = [name for name in FEATURES if name not in data.columns]
    if missing_features:
        raise KeyError(f"Expected feature columns are missing: {missing_features}")

    labels = data["dendrite_type"].value_counts().reindex(["aspiny", "spiny"])
    missing = (
        data[list(FEATURES)]
        .isna()
        .mean()
        .mul(100)
        .rename("missing_percent")
        .rename_axis("feature")
        .reset_index()
    )
    missing["feature_label"] = missing["feature"].map(FEATURES)
    missing.to_csv(RESULT_DIR / "feature_missingness.csv", index=False)

    line_counts = pd.crosstab(data["line_name"], data["dendrite_type"])
    line_counts["n_cells"] = line_counts.sum(axis=1)
    line_counts["n_labels"] = (line_counts[["aspiny", "spiny"]] > 0).sum(axis=1)
    line_counts.sort_values("n_cells", ascending=False).to_csv(
        RESULT_DIR / "mouse_line_by_label.csv"
    )

    two_label_lines = int((line_counts["n_labels"] == 2).sum())
    one_label_lines = int((line_counts["n_labels"] == 1).sum())
    summary = [
        "CHIP 705 neuron project: initial data profile",
        f"Rows in primary cohort: {len(data):,}",
        f"Unique specimen IDs: {data['specimen_id'].nunique():,}",
        f"Class counts: {labels.to_dict()}",
        f"Mouse lines represented: {len(line_counts):,}",
        f"Lines containing both labels: {two_label_lines:,}",
        f"Lines containing only one label: {one_label_lines:,}",
        "",
        "Missing values in candidate predictors:",
        missing[["feature_label", "missing_percent"]].to_string(index=False),
        "",
        "Interpretation note: mouse line and dendrite label may be associated. Do not use mouse line as a predictor. A random cell-level split may overstate performance; use grouped validation by mouse line if feasible.",
    ]
    (RESULT_DIR / "eda_summary.txt").write_text("\n".join(summary), encoding="utf-8")

    sns.set_theme(style="whitegrid", context="notebook", font_scale=1.0)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(data=data, x="dendrite_type", order=["aspiny", "spiny"], color="#2B7A78", ax=ax)
    ax.set(title="Mouse neuron labels in the analysis cohort", xlabel="Dendrite type", ylabel="Number of cells")
    for container in ax.containers:
        ax.bar_label(container, fmt="%d", padding=3)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "class_distribution.png", dpi=220)
    plt.close(fig)

    plot_features = ["ef__vrest", "ef__avg_firing_rate", "ef__ri", "ef__tau"]
    plot_data = data.melt(
        id_vars="dendrite_type",
        value_vars=plot_features,
        var_name="feature",
        value_name="value",
    ).dropna()
    plot_data["feature_label"] = plot_data["feature"].map(FEATURES)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for ax, feature in zip(axes.flat, plot_features):
        subset = plot_data.loc[plot_data["feature"] == feature]
        sns.boxplot(
            data=subset,
            x="dendrite_type",
            y="value",
            order=["aspiny", "spiny"],
            color="#79B4A9",
            showfliers=False,
            ax=ax,
        )
        ax.set(title=FEATURES[feature], xlabel="Dendrite type", ylabel=FEATURES[feature])
    fig.suptitle("Selected electrophysiology features by dendrite type", y=1.02)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "feature_distributions.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    print("Initial data profile complete.")
    print(f"Cohort: {len(data):,} cells; class counts: {labels.to_dict()}")
    print(f"Mouse lines: {len(line_counts)}; both labels: {two_label_lines}; one label only: {one_label_lines}")
    print(f"Outputs saved in {RESULT_DIR} and {FIGURE_DIR}")


if __name__ == "__main__":
    main()
