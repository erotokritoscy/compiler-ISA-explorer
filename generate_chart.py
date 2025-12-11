import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('results/summary_table.csv')

metrics = ["exec time", "energy", "peak power", "code size", "CPU area"]

default_vals = df[df["params"] == "default"].iloc[0][metrics]
best_vals = df[metrics].min()

plot_df = pd.DataFrame({
    "default": default_vals,
    "brute force (best)": best_vals,
    "local search (best)": best_vals
}, index=metrics)

best_params = {m: df.loc[df[m].idxmin(), "params"] for m in metrics}

# Increase global font sizes
plt.rcParams.update({
    "font.size": 16,
    "axes.titlesize": 22,
    "axes.labelsize": 18,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 16,
    "legend.title_fontsize": 18
})

# Figure
fig = plt.figure(figsize=(17,13))
gs = fig.add_gridspec(2, 1, height_ratios=[3, 1])

ax = fig.add_subplot(gs[0])
ax_table = fig.add_subplot(gs[1])

# Chart
plot_df.plot(kind="bar", log=True, ax=ax)
ax.set_title("Default vs Best (Brute Force & Local Search)")
ax.set_xticklabels(metrics, rotation=45, ha="right")
ax.legend(title="Configuration")

def fmt_value(metric, val):
    if metric in ["exec time", "energy"]:
        return f"{val:.8f}"
    else:
        return f"{val:.6g}"

# Big value labels
for container in ax.containers:
    for bar, val in zip(container, container.datavalues):
        idx = int(round(bar.get_x() + bar.get_width()/2))
        metric = plot_df.index[idx]
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            fmt_value(metric, val),
            rotation=30,
            ha="center",
            va="bottom",
            fontsize=16
        )

# Table
ax_table.axis("off")
table_data = [[m, best_params[m]] for m in metrics]
table = ax_table.table(
    cellText=table_data,
    colLabels=["Metric", "Best Parameter Combination"],
    loc="center"
)
table.auto_set_font_size(False)
table.set_fontsize(16)
table.scale(1, 2.2)
ax_table.set_title("Best Parameter Combination per Metric", fontsize=20)

plt.tight_layout()

# Save
png_path = "results/default_vs_best_3bars.png"
pdf_path = "results/default_vs_best_3bars.pdf"
plt.savefig(png_path, dpi=300, bbox_inches="tight")
plt.savefig(pdf_path, bbox_inches="tight")
plt.close()

png_path, pdf_path
