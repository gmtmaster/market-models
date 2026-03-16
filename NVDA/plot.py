import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv("data/nvda_regime_features.csv")
summary = pd.read_csv("data/nvda_regime_summary.csv")

df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime").reset_index(drop=True)

# Regime order
regime_order = ["Low Vol", "Medium Vol", "High Vol"]
summary["vol_regime"] = pd.Categorical(summary["vol_regime"], categories=regime_order, ordered=True)
summary = summary.sort_values("vol_regime")

# Colors
colors = {
    "Low Vol": "green",
    "Medium Vol": "orange",
    "High Vol": "red"
}

# -----------------------------
# Create report layout
# -----------------------------
fig, axes = plt.subplots(4, 1, figsize=(16, 18))

# =====================================================
# 1. NVDA Price colored by volatility regime
# =====================================================
ax1 = axes[0]

for regime, color in colors.items():
    subset = df[df["vol_regime"] == regime]
    ax1.scatter(
        subset["datetime"],
        subset["close"],
        s=8,
        color=color,
        label=regime,
        alpha=0.7
    )

ax1.set_title("NVDA Close Price by Volatility Regime", fontsize=14)
ax1.set_ylabel("Close Price")
ax1.legend()
ax1.grid(True)

# =====================================================
# 2. Rolling volatility
# =====================================================
ax2 = axes[1]

ax2.plot(df["datetime"], df["vol_20d"], linewidth=1.5)

ax2.set_title("20-Day Realized Volatility (Annualized)", fontsize=14)
ax2.set_ylabel("Volatility")
ax2.grid(True)

# =====================================================
# 3. Avg next-day range
# =====================================================
ax3 = axes[2]

ax3.bar(
    summary["vol_regime"],
    summary["avg_next_day_range"]
)

ax3.set_title("Average Next-Day Range by Regime", fontsize=14)
ax3.set_ylabel("Next-Day Range")
ax3.grid(True, axis="y")

# =====================================================
# 4. Return distribution
# =====================================================
ax4 = axes[3]

box_data = [
    df[df["vol_regime"] == "Low Vol"]["return"].dropna(),
    df[df["vol_regime"] == "Medium Vol"]["return"].dropna(),
    df[df["vol_regime"] == "High Vol"]["return"].dropna()
]

ax4.boxplot(box_data, labels=regime_order)

ax4.set_title("Daily Return Distribution by Regime", fontsize=14)
ax4.set_ylabel("Daily Return")
ax4.grid(True)

# -----------------------------
# Final layout
# -----------------------------
plt.tight_layout()

# Save high-quality image for GitHub
plt.savefig("nvda_volatility_research_report.png", dpi=300)

plt.show()