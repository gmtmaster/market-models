# 📊 NVDA Volatility Regime Classification

A quantitative research project exploring **volatility regime behaviour in NVIDIA (NVDA)** using rolling statistical features derived from historical daily price data.

The objective is to identify periods of **high-volatility vs low-volatility market states** and observe how regime transitions emerge over time.

---

## 🎯 Research Objective

To classify daily market conditions into simple volatility regimes by using rolling price-derived features such as:

* daily returns
* rolling volatility
* rolling mean return
* price range behaviour

This allows a clearer view of how market conditions evolve between stable and unstable phases.

---

## 🧠 Methodology

The model uses rolling-window calculations on historical NVDA daily OHLCV data:

* Return = daily close-to-close percentage move
* Rolling Volatility = standard deviation of returns
* Rolling Mean Return = short-term trend estimate
* Intraday Range = high-low expansion

A threshold-based logic is then applied to classify observations into:

* **Low Vol**
* **High Vol**

---

## 🧰 Tools Used

`Python` • `Pandas` • `NumPy` • `Matplotlib`

---

## 📂 Files

```bash id="xf27yt"
nvda_vol_regime.py
plot.py
data/
├── nvda_data.csv
├── nvda_regime_features.csv
├── nvda_regime_summary.csv
```

---

## 📈 Output

The project produces:

* rolling regime features dataset
* regime summary table
* visual volatility report

---

## 📉 Research Chart

The generated chart highlights:

* price development
* rolling volatility changes
* regime shifts over time

---

## 🔍 Key Observation

Volatility tends to cluster rather than distribute evenly.

Periods classified as **High Vol** often appear during:

* strong directional moves
* rapid price repricing
* event-driven market behaviour

Low-volatility phases often precede regime expansion.

---

## 📌 Why This Matters

Understanding volatility regimes helps frame:

* position sizing logic
* risk environment
* timing sensitivity
* broader market condition awareness

---

### 💬 Research Note

> Volatility is often less random than it first appears — regimes reveal hidden structure.
