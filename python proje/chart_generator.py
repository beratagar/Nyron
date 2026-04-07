# -*- coding: utf-8 -*-
"""Grafik oluşturma modülü"""

import matplotlib.pyplot as plt
import numpy as np


def _figure_canvas_qt():
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

    return FigureCanvasQTAgg


class ChartGenerator:
    """Hisse senedi grafiklerini oluşturur"""

    def __init__(self, dark: bool = True):
        self.dark = bool(dark)
        # Matplotlib style/colors must follow app theme; otherwise light UI shows dark charts.
        if self.dark:
            plt.style.use("dark_background")
        else:
            # Aydınlık tema için Matplotlib varsayılanlarını baz al.
            plt.style.use("default")
        self.fig = None
        self.canvas = None
        if self.dark:
            self.colors = {
                "bg": "#08111c",
                "panel": "#0d1826",
                "grid": "#284056",
                "text": "#e7eef7",
                "muted": "#8ea6bf",
                "up": "#57d38c",
                "down": "#ff7b7b",
                "sma20": "#ffbf69",
                "sma50": "#70a1ff",
                "avg": "#f4d35e",
                "blue": "#70a1ff",
                "rsi": "#9b8cff",
                "signal": "#ff9f68",
                "macd": "#63cdda",
                "hint_bg": "#0b1521",
            }
        else:
            # Light theme palette: higher contrast text, neutral panels, soft grid.
            self.colors = {
                "bg": "#ffffff",
                "panel": "#ffffff",
                "grid": "#cbd5e1",
                "text": "#0f172a",
                "muted": "#475569",
                "up": "#0d9f73",
                "down": "#c62828",
                "sma20": "#b45309",   # amber/brown
                "sma50": "#1d4ed8",   # blue
                "avg": "#a16207",     # gold-ish
                "blue": "#1d4ed8",
                "rsi": "#6d28d9",     # purple
                "signal": "#c2410c",  # orange
                "macd": "#0f766e",    # teal
                "hint_bg": "#f1f5f9",
            }
        self.lookback_days = 60

    def _build_figure(self, df, ticker):
        self.lookback_days = self._recommended_lookback(df)
        self.fig = plt.figure(figsize=(14.5, 8.6), dpi=100, facecolor=self.colors["bg"])
        gs = self.fig.add_gridspec(3, 2, height_ratios=[3.9, 1.15, 1.0], hspace=0.24, wspace=0.12)
        ax1 = self.fig.add_subplot(gs[0, :])
        ax2 = self.fig.add_subplot(gs[1, :], sharex=ax1)
        ax3 = self.fig.add_subplot(gs[2, 0], sharex=ax1)
        ax4 = self.fig.add_subplot(gs[2, 1], sharex=ax1)

        self._style_axes(ax1, title=f"{ticker} | Son {self.lookback_days} Gün Teknik Harita")
        self._style_axes(ax2, title="Hacim Akışı")
        self._style_axes(ax3, title="RSI Bölgesi")
        self._style_axes(ax4, title="MACD Nabzı")

        self._plot_candlestick(ax1, df, ticker)
        self._plot_volume(ax2, df)
        self._plot_rsi(ax3, df)
        self._plot_macd(ax4, df)
        self._format_xaxis(ax4, df)

        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), visible=False)
        self.fig.subplots_adjust(left=0.06, right=0.985, top=0.95, bottom=0.08)

    def create_candlestick_chart(self, df, ticker, parent_widget):
        """Mum grafiği oluştur (Tkinter)."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self._build_figure(df, ticker)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_widget)
        self.canvas.draw()
        return self.canvas.get_tk_widget()

    def create_candlestick_chart_qt(self, df, ticker):
        """PySide6 için FigureCanvas döndürür."""
        self.close()
        self._build_figure(df, ticker)
        FigureCanvasQTAgg = _figure_canvas_qt()
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.draw()
        return self.canvas

    def _recommended_lookback(self, df):
        """Grafik için mantıklı zaman aralığını belirle"""
        total = len(df)
        if total >= 140:
            return 90
        if total >= 90:
            return 75
        if total >= 60:
            return 60
        return max(30, total)

    def _style_axes(self, ax, title=""):
        ax.set_facecolor(self.colors["panel"])
        for spine in ax.spines.values():
            spine.set_color(self.colors["grid"])
            spine.set_linewidth(1)
        ax.tick_params(colors=self.colors["muted"], labelsize=9)
        ax.grid(True, color=self.colors["grid"], alpha=0.22, linewidth=0.8)
        if title:
            ax.set_title(title, fontsize=12, fontweight="bold", color=self.colors["text"], loc="left", pad=12)

    def _plot_candlestick(self, ax, df, ticker):
        df = df.copy()
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        plot_df = df.tail(self.lookback_days)
        x = np.arange(len(plot_df))

        colors = [self.colors["up"] if row["Close"] >= row["Open"] else self.colors["down"] for _, row in plot_df.iterrows()]
        candle_width = 0.58

        for i, (_, row) in enumerate(plot_df.iterrows()):
            body_color = colors[i]
            ax.plot([i, i], [row["Low"], row["High"]], color=body_color, linewidth=1.15, alpha=0.95, zorder=2)
            height = max(abs(row["Close"] - row["Open"]), 0.01)
            bottom = min(row["Open"], row["Close"])
            ax.bar(i, height, bottom=bottom, color=body_color, width=candle_width, edgecolor=body_color, linewidth=0.6, zorder=3)

        ax.plot(x, plot_df["SMA20"], label="SMA 20", color=self.colors["sma20"], linewidth=1.8, alpha=0.95, zorder=4)
        ax.plot(x, plot_df["SMA50"], label="SMA 50", color=self.colors["sma50"], linewidth=1.8, alpha=0.95, zorder=4)

        support, resistance = self._calculate_support_resistance(plot_df)
        self._draw_levels(ax, support, self.colors["up"])
        self._draw_levels(ax, resistance, self.colors["down"])

        trend_direction = self._determine_trend(plot_df)
        trend_label = {"up": "Yükseliş", "down": "Düşüş", "sideways": "Yatay"}[trend_direction]
        trend_color = {"up": self.colors["up"], "down": self.colors["down"], "sideways": self.colors["avg"]}[trend_direction]
        last_close = plot_df["Close"].iloc[-1]
        change_pct = ((plot_df["Close"].iloc[-1] - plot_df["Close"].iloc[0]) / plot_df["Close"].iloc[0]) * 100
        ax.text(
            0.99,
            0.98,
            f"Trend: {trend_label} | Son: {last_close:.2f} TL | {self.lookback_days}G: {change_pct:+.2f}%",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=10,
            color=trend_color,
            bbox={
                "facecolor": self.colors["hint_bg"],
                "edgecolor": self.colors["grid"],
                "boxstyle": "round,pad=0.45",
                "alpha": 0.95,
            },
        )

        ax.set_ylabel("Fiyat (TL)", color=self.colors["muted"], fontsize=10)
        ax.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=self.colors["text"])
        ax.set_xlim(-1, len(plot_df))

    def _draw_levels(self, ax, levels, color):
        for idx, level in enumerate(levels):
            line_width = 1.55 if idx == 0 else 1.15
            alpha = 0.82 if idx == 0 else 0.55
            ax.axhline(level, color=color, linestyle=(0, (4, 4)), linewidth=line_width, alpha=alpha)

    def _calculate_support_resistance(self, df):
        closes = df["Close"].values
        lows = df["Low"].values
        highs = df["High"].values

        support = []
        for i in range(5, len(lows) - 5):
            if lows[i] == min(lows[i - 5 : i + 5]):
                support.append(lows[i])

        support = sorted(list(set(round(value, 2) for value in support)))
        support = [value for idx, value in enumerate(support) if idx == 0 or abs(value - support[idx - 1]) > closes.mean() * 0.02][:3]

        resistance = []
        for i in range(5, len(highs) - 5):
            if highs[i] == max(highs[i - 5 : i + 5]):
                resistance.append(highs[i])

        resistance = sorted(list(set(round(value, 2) for value in resistance)), reverse=True)
        resistance = [value for idx, value in enumerate(resistance) if idx == 0 or abs(value - resistance[idx - 1]) > closes.mean() * 0.02][:3]
        return support, resistance

    def _determine_trend(self, df):
        if len(df) < 10:
            return "sideways"

        recent_avg = df["Close"].tail(10).mean()
        earlier_avg = df["Close"].head(10).mean()
        sma20 = df["SMA20"].iloc[-1]
        sma50 = df["SMA50"].iloc[-1]

        if sma20 > sma50 and recent_avg > earlier_avg:
            return "up"
        if sma20 < sma50 and recent_avg < earlier_avg:
            return "down"
        return "sideways"

    def _plot_volume(self, ax, df):
        plot_df = df.tail(self.lookback_days)
        x = np.arange(len(plot_df))
        colors = [self.colors["up"] if plot_df["Close"].iloc[i] >= plot_df["Open"].iloc[i] else self.colors["down"] for i in range(len(plot_df))]
        avg_volume = plot_df["Volume"].mean()
        spikes = plot_df["Volume"] > avg_volume * 1.5

        bar_colors = [self.colors["avg"] if spikes.iloc[i] else colors[i] for i in range(len(plot_df))]
        ax.bar(x, plot_df["Volume"], color=bar_colors, alpha=0.72, width=0.8)
        ax.plot(x, plot_df["Volume"].rolling(10).mean(), color=self.colors["blue"], linewidth=1.4, alpha=0.85, label="Ort 10")
        ax.axhline(avg_volume, color=self.colors["avg"], linestyle=(0, (3, 4)), linewidth=1.1, alpha=0.8, label=f"Ort {avg_volume:,.0f}")
        ax.set_ylabel("Hacim", color=self.colors["muted"], fontsize=10)
        ax.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=self.colors["text"])
        ax.set_xlim(-1, len(plot_df))

    def _plot_rsi(self, ax, df):
        if "RSI" not in df.columns:
            ax.text(0.5, 0.5, "RSI verisi yok", ha="center", va="center", transform=ax.transAxes, color=self.colors["muted"])
            return

        plot_df = df.tail(self.lookback_days).dropna(subset=["RSI"])
        if plot_df.empty:
            ax.text(0.5, 0.5, "Yeterli RSI verisi yok", ha="center", va="center", transform=ax.transAxes, color=self.colors["muted"])
            return

        x = np.arange(len(plot_df))
        rsi = plot_df["RSI"]

        ax.fill_between(x, 70, 100, color=self.colors["down"], alpha=0.08)
        ax.fill_between(x, 30, 70, color=self.colors["avg"], alpha=0.08)
        ax.fill_between(x, 0, 30, color=self.colors["up"], alpha=0.08)
        ax.plot(x, rsi, color=self.colors["rsi"], linewidth=2.1, label="RSI")
        ax.axhline(70, color=self.colors["down"], linestyle=(0, (3, 4)), linewidth=1)
        ax.axhline(50, color=self.colors["muted"], linestyle=":", linewidth=0.9)
        ax.axhline(30, color=self.colors["up"], linestyle=(0, (3, 4)), linewidth=1)
        ax.text(0.99, 0.85, f"Son RSI: {rsi.iloc[-1]:.1f}", transform=ax.transAxes, ha="right", color=self.colors["text"], fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_ylabel("RSI", color=self.colors["muted"], fontsize=10)
        ax.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=self.colors["text"])

    def _plot_macd(self, ax, df):
        if "MACD" not in df.columns:
            ax.text(0.5, 0.5, "MACD verisi yok", ha="center", va="center", transform=ax.transAxes, color=self.colors["muted"])
            return

        plot_df = df.tail(self.lookback_days).dropna(subset=["MACD"])
        if plot_df.empty:
            ax.text(0.5, 0.5, "Yeterli MACD verisi yok", ha="center", va="center", transform=ax.transAxes, color=self.colors["muted"])
            return

        x = np.arange(len(plot_df))
        macd = plot_df["MACD"]
        signal = plot_df["MACD_Signal"] if "MACD_Signal" in plot_df.columns else plot_df["MACD"] * 0
        histogram = macd - signal
        hist_colors = [self.colors["up"] if value >= 0 else self.colors["down"] for value in histogram]

        ax.bar(x, histogram, color=hist_colors, alpha=0.42, width=0.72, label="Histogram")
        ax.plot(x, macd, color=self.colors["macd"], linewidth=1.9, label="MACD")
        ax.plot(x, signal, color=self.colors["signal"], linewidth=1.7, label="Signal")
        ax.axhline(0, color=self.colors["muted"], linestyle=":", linewidth=0.9)
        ax.text(0.99, 0.85, f"Fark: {(macd.iloc[-1] - signal.iloc[-1]):+.4f}", transform=ax.transAxes, ha="right", color=self.colors["text"], fontsize=9)
        ax.set_ylabel("MACD", color=self.colors["muted"], fontsize=10)
        ax.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=self.colors["text"])

    def _format_xaxis(self, ax, df):
        plot_df = df.tail(self.lookback_days)
        labels = [index.strftime("%d %b") if hasattr(index, "strftime") else str(index)[:10] for index in plot_df.index]
        step = max(1, len(labels) // 6)
        ticks = np.arange(0, len(labels), step)
        ax.set_xticks(ticks)
        ax.set_xticklabels([labels[i] for i in ticks], rotation=0, ha="center", color=self.colors["muted"])

    def close(self):
        """Grafiği kapat"""
        if self.fig:
            plt.close(self.fig)
            self.fig = None
            self.canvas = None
