from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


FEATURE_COLUMNS = [
    "NDVI",
    "NDBI",
    "built_up",
    "vegetation_deficit",
    "air_temperature",
    "relative_humidity",
    "wind_speed",
]


@dataclass
class ModelResult:
    model: Pipeline
    rows_used: int
    r2: float | None
    mae: float | None
    rmse: float | None
    feature_importance: dict[str, float]
    grouped_importance: dict[str, float]
    sensitivities: dict[str, float]


def _empty_importance() -> dict[str, float]:
    return {name: 0.0 for name in FEATURE_COLUMNS}


def train_lst_model(samples: list[dict[str, Any]]) -> ModelResult:
    """Train a RandomForestRegressor on GEE sampled driver rows."""
    frame = pd.DataFrame(samples)
    if frame.empty or "LST" not in frame:
        return _fallback_model()

    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=["LST"])
    for column in FEATURE_COLUMNS:
        if column not in frame:
            frame[column] = np.nan

    usable = frame[FEATURE_COLUMNS + ["LST"]].copy()
    usable = usable.dropna(subset=["LST"])
    if len(usable) < 20:
        return _fallback_model(usable)

    x = usable[FEATURE_COLUMNS]
    y = usable["LST"]

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "forest",
                RandomForestRegressor(
                    n_estimators=160,
                    max_depth=14,
                    min_samples_leaf=3,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    r2: float | None = None
    mae: float | None = None
    rmse: float | None = None
    if len(usable) >= 60:
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.25, random_state=42
        )
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        r2 = float(r2_score(y_test, predictions))
        mae = float(mean_absolute_error(y_test, predictions))
        rmse = float(mean_squared_error(y_test, predictions) ** 0.5)
        model.fit(x, y)
    else:
        model.fit(x, y)

    forest = model.named_steps["forest"]
    raw_importance = {
        name: float(value)
        for name, value in zip(FEATURE_COLUMNS, forest.feature_importances_)
    }
    grouped = _group_importance(raw_importance)
    sensitivities = estimate_sensitivities(model, x)

    return ModelResult(
        model=model,
        rows_used=int(len(usable)),
        r2=r2,
        mae=mae,
        rmse=rmse,
        feature_importance=raw_importance,
        grouped_importance=grouped,
        sensitivities=sensitivities,
    )


def estimate_sensitivities(model: Pipeline, x: pd.DataFrame) -> dict[str, float]:
    """Estimate local scenario sensitivities with small controlled perturbations."""
    if x.empty:
        return {"ndvi_cooling_per_0_1": 1.2, "built_up_warming_per_0_1": 0.8}

    base = x[FEATURE_COLUMNS].copy()
    base_prediction = model.predict(base)

    greener = base.copy()
    greener["NDVI"] = (greener["NDVI"] + 0.10).clip(-1, 1)
    greener["vegetation_deficit"] = (1 - ((greener["NDVI"] + 1) / 2)).clip(0, 1)
    greener_prediction = model.predict(greener)
    ndvi_cooling = float(np.nanmean(base_prediction - greener_prediction))

    less_built = base.copy()
    less_built["built_up"] = (less_built["built_up"] - 0.10).clip(0, 1)
    less_built["NDBI"] = (less_built["NDBI"] - 0.10).clip(-1, 1)
    less_built_prediction = model.predict(less_built)
    built_up_effect = float(np.nanmean(base_prediction - less_built_prediction))

    return {
        "ndvi_cooling_per_0_1": max(0.25, abs(ndvi_cooling)),
        "built_up_warming_per_0_1": max(0.20, abs(built_up_effect)),
    }


def _group_importance(raw: dict[str, float]) -> dict[str, float]:
    vegetation = raw.get("NDVI", 0.0) + raw.get("vegetation_deficit", 0.0)
    built_up = raw.get("NDBI", 0.0) + raw.get("built_up", 0.0)
    meteorology = (
        raw.get("air_temperature", 0.0)
        + raw.get("relative_humidity", 0.0)
        + raw.get("wind_speed", 0.0)
    )
    total = vegetation + built_up + meteorology
    if total <= 0:
        return {"vegetation": 0.34, "built_up": 0.33, "meteorology": 0.33}
    return {
        "vegetation": round(vegetation / total, 4),
        "built_up": round(built_up / total, 4),
        "meteorology": round(meteorology / total, 4),
    }


def _fallback_model(frame: pd.DataFrame | None = None) -> ModelResult:
    """Return a tiny fitted model so scenario code can still execute in demos."""
    if frame is None or frame.empty:
        frame = pd.DataFrame(
            {
                "NDVI": [0.05, 0.25, 0.45, 0.15],
                "NDBI": [0.45, 0.25, 0.05, 0.35],
                "built_up": [0.85, 0.60, 0.25, 0.75],
                "vegetation_deficit": [0.70, 0.50, 0.25, 0.60],
                "air_temperature": [32.0, 31.0, 30.0, 33.0],
                "relative_humidity": [58.0, 64.0, 72.0, 54.0],
                "wind_speed": [2.0, 2.5, 3.2, 1.8],
                "LST": [41.0, 36.5, 32.5, 39.0],
            }
        )
    for column in FEATURE_COLUMNS:
        if column not in frame:
            frame[column] = np.nan
    if "LST" not in frame:
        frame["LST"] = 36.0

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "forest",
                RandomForestRegressor(n_estimators=40, random_state=42, min_samples_leaf=1),
            ),
        ]
    )
    model.fit(frame[FEATURE_COLUMNS], frame["LST"])
    raw = _empty_importance()
    raw.update({"NDVI": 0.22, "NDBI": 0.23, "built_up": 0.18, "vegetation_deficit": 0.18, "air_temperature": 0.09, "relative_humidity": 0.06, "wind_speed": 0.04})
    return ModelResult(
        model=model,
        rows_used=int(len(frame)),
        r2=None,
        mae=None,
        rmse=None,
        feature_importance=raw,
        grouped_importance=_group_importance(raw),
        sensitivities={"ndvi_cooling_per_0_1": 1.2, "built_up_warming_per_0_1": 0.8},
    )
