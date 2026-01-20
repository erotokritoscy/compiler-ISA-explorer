import pandas as pd
import matplotlib.pyplot as plt


def generate_chart(title):
    # Load data
    df = pd.read_csv("results/summary_table.csv")

    # ---- Unit conversions ----
    df["exec time (µs)"] = df["exec time"] * 1e6
    df["energy (µJ)"] = df["energy"] * 1e6
    df["peak power (mW)"] = df["peak power"] * 1e3

    metrics = [
        "exec time (µs)",
        "energy (µJ)",
        "peak power (mW)",
        "code size",
        "CPU area",
    ]

    default_vals = df[df["params"] == "default"].iloc[0][metrics]
    best_vals = df[metrics].min()

    plot_df = pd.DataFrame(
        {
            "default": default_vals,
            "brute force (best)": best_vals,
            "local search (best)": best_vals,
        },
        index=metrics,
    )

    best_params = {m: df.loc[df[m].idxmin(), "params"] for m in metrics}

    # ---- Global font sizes ----
    plt.rcParams.update(
        {
            "font.size": 16,
            "axes.titlesize": 22,
            "axes.labelsize": 18,
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "legend.fontsize": 16,
            "legend.title_fontsize": 18,
        }
    )

    # ---- Figure + layout ----
    fig = plt.figure(figsize=(17, 15))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.4])

    ax = fig.add_subplot(gs[0])
    ax_table = fig.add_subplot(gs[1])

    # ---- Bar chart ----
    plot_df.plot(kind="bar", log=True, ax=ax)
    ax.set_title(title)
    ax.set_xticklabels(metrics, rotation=45, ha="right")
    ax.legend(title="Configuration")

    def fmt_value(metric, val):
        return f"{val:.6g}"

    for container in ax.containers:
        for bar, val in zip(container, container.datavalues):
            idx = int(round(bar.get_x() + bar.get_width() / 2))
            metric = plot_df.index[idx]
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                fmt_value(metric, val),
                rotation=30,
                ha="center",
                va="bottom",
                fontsize=16,
            )

    # ---- Table ----
    ax_table.axis("off")

    table_data = [[m, best_params[m]] for m in metrics]

    table = ax_table.table(
        cellText=table_data,
        colLabels=["Metric", "Best Parameter Combination"],
        loc="center",
        colWidths=[0.25, 0.75],
    )

    table.auto_set_font_size(False)
    table.set_fontsize(16)

    # Enable text wrapping and proper row height
    for (_, _), cell in table.get_celld().items():
        cell.get_text().set_wrap(True)

    for row in range(len(table_data) + 1):  # +1 for header
        for col in range(2):
            table[(row, col)].set_height(0.18)

    # ax_table.set_title("Best Parameter Combination per Metric", fontsize=20)
    plt.tight_layout()

    # ---- Save ----
    png_path = "results/default_vs_best_3bars.png"
    pdf_path = "results/default_vs_best_3bars.pdf"
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()
