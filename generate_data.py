"""
製造ラインの生産実績データを生成するスクリプト。

このプロジェクトはポートフォリオ用のため、実データではなく
実務経験（生産管理・品質管理）をもとにした仮想データを
統計的な特性を持たせて生成しています。

生成するデータ:
- 3本の生産ライン（A, B, C）× 90日分の日次実績
- 計画生産数、実績生産数、不良数、計画稼働時間、実際の稼働時間
- 不良原因（カテゴリ別）の内訳

乱数シードを固定しているため、何度実行しても同じデータが生成されます。
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

LINES = {
    # ライン名: (基準生産数/日, 生産数のばらつき, 基準不良率, 基準稼働率)
    "Aライン": {"base_output": 1200, "output_std": 60, "base_defect_rate": 0.018, "base_availability": 0.94},
    "Bライン": {"base_output": 950, "output_std": 45, "base_defect_rate": 0.032, "base_availability": 0.89},
    "Cライン": {"base_output": 1400, "output_std": 70, "base_defect_rate": 0.024, "base_availability": 0.91},
}

DEFECT_CAUSES = ["材料不良", "設備調整不足", "作業ミス", "治具摩耗", "その他"]
# ラインごとに主要な不良原因の傾向を変える（Bラインは設備調整不足が多い、など）
DEFECT_CAUSE_WEIGHTS = {
    "Aライン": [0.30, 0.20, 0.25, 0.15, 0.10],
    "Bライン": [0.15, 0.45, 0.15, 0.15, 0.10],
    "Cライン": [0.25, 0.20, 0.30, 0.15, 0.10],
}

N_DAYS = 90
START_DATE = datetime(2026, 5, 1)
PLANNED_MINUTES_PER_DAY = 8 * 60  # 8時間稼働想定


def generate_daily_records():
    records = []
    dates = [START_DATE + timedelta(days=i) for i in range(N_DAYS)]

    for line_name, params in LINES.items():
        # ラインごとに緩やかな改善トレンド（不良率が徐々に下がる）を持たせる
        improvement_trend = np.linspace(1.15, 0.85, N_DAYS)

        for day_idx, date in enumerate(dates):
            is_weekend = date.weekday() >= 5
            if is_weekend:
                continue  # 土日は非稼働と仮定

            # 計画生産数（日によって多少の変動あり）
            planned_output = int(params["base_output"] * rng.normal(1.0, 0.03))

            # 稼働率（設備トラブル等でたまに大きく落ちる日を混ぜる）
            availability = params["base_availability"] + rng.normal(0, 0.02)
            if rng.random() < 0.05:  # 5%の確率で設備トラブル発生
                availability -= rng.uniform(0.10, 0.25)
            availability = float(np.clip(availability, 0.4, 1.0))

            actual_minutes = PLANNED_MINUTES_PER_DAY * availability

            # 実績生産数（稼働時間に比例させつつ、ばらつきを加える）
            actual_output = int(
                planned_output * availability * rng.normal(1.0, 0.02)
            )
            actual_output = max(actual_output, 0)

            # 不良率（緩やかな改善トレンド × ランダム変動）
            defect_rate = params["base_defect_rate"] * improvement_trend[day_idx]
            defect_rate *= rng.normal(1.0, 0.15)
            defect_rate = float(np.clip(defect_rate, 0.001, 0.15))

            defect_qty = int(round(actual_output * defect_rate))
            good_qty = actual_output - defect_qty

            record = {
                "date": date.strftime("%Y-%m-%d"),
                "line": line_name,
                "planned_output_qty": planned_output,
                "actual_output_qty": actual_output,
                "good_qty": good_qty,
                "defect_qty": defect_qty,
                "planned_minutes": PLANNED_MINUTES_PER_DAY,
                "actual_operating_minutes": round(actual_minutes, 1),
            }
            records.append(record)

            # 不良原因の内訳（defect_qty を原因カテゴリに配分）
            if defect_qty > 0:
                weights = DEFECT_CAUSE_WEIGHTS[line_name]
                cause_counts = rng.multinomial(defect_qty, weights)
                for cause, count in zip(DEFECT_CAUSES, cause_counts):
                    if count > 0:
                        defect_detail_records.append(
                            {
                                "date": date.strftime("%Y-%m-%d"),
                                "line": line_name,
                                "defect_cause": cause,
                                "count": int(count),
                            }
                        )

    return pd.DataFrame(records)


defect_detail_records = []


def generate_defect_detail_df():
    return pd.DataFrame(defect_detail_records)


if __name__ == "__main__":
    daily_df = generate_daily_records()
    defect_df = generate_defect_detail_df()

    daily_df.to_csv("data/production_daily.csv", index=False, encoding="utf-8-sig")
    defect_df.to_csv("data/defect_detail.csv", index=False, encoding="utf-8-sig")

    print(f"production_daily.csv: {len(daily_df)} 行")
    print(f"defect_detail.csv: {len(defect_df)} 行")
