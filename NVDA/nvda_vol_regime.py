import pandas as pd
import numpy as np


def load_data(file_path="/data/nvda_data.csv"):
    df = pd.read_csv(file_path)

    # dátum beolvasása stringként, majd explicit formátummal átalakítva
    df["datetime"] = pd.to_datetime(df["datetime"].astype(str), format="%Y%m%d")

    # időrend
    df = df.sort_values("datetime").reset_index(drop=True)

    return df


def create_features(df):
    # napi hozam, ha esetleg nem lenne benne vagy újra akarjuk számolni
    df["return"] = df["close"].pct_change()

    # napi range százalékban
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]

    # 20 napos realized volatility (annualizálva)
    df["vol_20d"] = df["return"].rolling(20).std() * np.sqrt(252)

    # következő napi return
    df["next_return"] = df["return"].shift(-1)

    # következő napi range
    df["next_range_pct"] = df["range_pct"].shift(-1)

    # egyszerű momentum jel: mai return előjele
    df["momentum_signal"] = np.where(df["return"] > 0, 1, 0)

    # mean reversion jel: nagy esés után másnap pozitív-e
    df["big_down_day"] = np.where(df["return"] < -0.02, 1, 0)

    return df


def classify_regimes(df):
    low_threshold = df["vol_20d"].quantile(0.33)
    high_threshold = df["vol_20d"].quantile(0.66)

    def regime_label(vol):
        if pd.isna(vol):
            return np.nan
        elif vol <= low_threshold:
            return "Low Vol"
        elif vol <= high_threshold:
            return "Medium Vol"
        else:
            return "High Vol"

    df["vol_regime"] = df["vol_20d"].apply(regime_label)

    return df


def create_summary_table(df):
    summary = df.groupby("vol_regime").agg(
        observations=("return", "count"),
        avg_daily_return=("return", "mean"),
        median_daily_return=("return", "median"),
        return_std=("return", "std"),
        avg_range_pct=("range_pct", "mean"),
        avg_next_day_return=("next_return", "mean"),
        avg_next_day_range=("next_range_pct", "mean")
    ).reset_index()

    return summary


def main():
    df = load_data("/data/nvda_data.csv")
    df = create_features(df)
    df = classify_regimes(df)

    # eldobjuk azokat a sorokat, ahol még nincs rolling vol
    df_clean = df.dropna(subset=["vol_20d", "next_return", "next_range_pct"]).copy()

    summary = create_summary_table(df_clean)

    print("\n=== REGIME SUMMARY ===")
    print(summary)

    df_clean.to_csv("nvda_regime_features.csv", index=False)
    summary.to_csv("nvda_regime_summary.csv", index=False)

    print("\nElkészült:")
    print("- nvda_regime_features.csv")
    print("- nvda_regime_summary.csv")


if __name__ == "__main__":
    main()