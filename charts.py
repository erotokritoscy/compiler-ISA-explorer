import re
import pandas as pd
import matplotlib.pyplot as plt


def sanitize_filename(s):
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)  # remove special chars
    s = re.sub(r"\s+", "_", s.strip())  # replace spaces with _
    return s


def generate_chart(title):
    # Load data
    df = pd.read_csv("results/summary_table.csv")

    # ---- Unit conversions ----
    df["exec time (µs)"] = df["exec time"] * 1e6
    df["energy (µJ)"] = df["energy"] * 1e6
    df["peak power (mW)"] = df["peak power"] * 1e3
    df["code size (bytes)"] = df["code size"]
    df["CPU area (cells)"] = df["CPU area"]

    metrics = [
        "exec time (µs)",
        "energy (µJ)",
        "peak power (mW)",
        "code size (bytes)",
        "CPU area (cells)",
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

    safe_title = sanitize_filename(title)

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

    def fmt_value(metric, val):
        return f"{val:.6g}"

    # =========================================================
    # 1. BAR CHART ONLY
    # =========================================================
    fig_chart, ax = plt.subplots(figsize=(17, 10))

    plot_df.plot(kind="bar", log=True, ax=ax)
    ax.set_title(title)
    ax.set_xticklabels(metrics, rotation=45, ha="right")
    ax.legend(title="Configuration")

    for container in ax.containers:
        for bar, val in zip(container, container.datavalues):
            x_center = bar.get_x() + bar.get_width() / 2
            metric_idx = int(round(x_center))
            metric_idx = max(0, min(metric_idx, len(plot_df.index) - 1))

            ax.text(
                x_center,
                bar.get_height(),
                fmt_value(plot_df.index[metric_idx], val),
                rotation=30,
                ha="center",
                va="bottom",
                fontsize=16,
            )

    plt.tight_layout()

    chart_png_path = f"results/{safe_title}_chart.png"
    chart_pdf_path = f"results/{safe_title}_chart.pdf"
    fig_chart.savefig(chart_png_path, dpi=300, bbox_inches="tight")
    fig_chart.savefig(chart_pdf_path, bbox_inches="tight")
    plt.close(fig_chart)

    # =========================================================
    # 2. TABLE ONLY
    # =========================================================
    fig_table, ax_table = plt.subplots(figsize=(17, 4.5))
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

    for (_, _), cell in table.get_celld().items():
        cell.get_text().set_wrap(True)

    for row in range(len(table_data) + 1):  # +1 for header
        for col in range(2):
            table[(row, col)].set_height(0.18)

    plt.tight_layout()

    table_png_path = f"results/{safe_title}_table.png"
    table_pdf_path = f"results/{safe_title}_table.pdf"
    fig_table.savefig(table_png_path, dpi=300, bbox_inches="tight")
    fig_table.savefig(table_pdf_path, bbox_inches="tight")
    plt.close(fig_table)


generate_chart("Default vs Best Configuration")
