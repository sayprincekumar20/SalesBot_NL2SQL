import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import re




#  statsmodels
try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception as e:
    ARIMA = None
    logging.warning("statsmodels not available; forecasting will be skipped.")







def _detect_time_and_value_columns(rows: List[Dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
    """
    Heuristic: pick the first column that looks like a period/date as time,
    and the first numeric column as value.
    """
    if not rows:
        return None, None

    sample = rows[0]
    keys = list(sample.keys())

    # time col candidates
    time_candidates = [k for k in keys if any(s in k.lower() for s in ["date", "year", "month", "period"])]
    time_col = time_candidates[0] if time_candidates else None

    # value col candidates (numeric-like)
    def is_num(x):
        return isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit())
    num_keys = []
    for k in keys:
        if all(is_num(r.get(k, None)) for r in rows if r.get(k, None) is not None):
            num_keys.append(k)
    value_col = None
    # prefer sales/revenue/amount/total
    for pref in ["sales", "revenue", "amount", "total", "value"]:
        vc = next((k for k in num_keys if pref in k.lower()), None)
        if vc:
            value_col = vc
            break
    if value_col is None and num_keys:
        value_col = num_keys[0]

    return time_col, value_col


# def forecast_arima(rows: List[Dict[str, Any]], horizon: int = 3) -> Optional[Dict[str, Any]]:
#     """
#     Fit simple ARIMA(1,1,1) and forecast `horizon` future points.
#     Expects rows sorted ascending by time.
#     """
#     if ARIMA is None:
#         return {"note": "statsmodels not installed; cannot run ARIMA."}

#     if not rows:
#         return {"note": "No data to forecast."}

#     tcol, vcol = _detect_time_and_value_columns(rows)
#     if not tcol or not vcol:
#         return {"note": f"Unable to detect time/value columns. Found time={tcol}, value={vcol}."}

#     try:
#         df = pd.DataFrame(rows)
#         # try to parse time column
#         try:
#             df[tcol] = pd.to_datetime(df[tcol])
#             df = df.sort_values(tcol)
#             idx = df[tcol]
#         except Exception:
#             # leave as is, but sort anyway
#             df = df.sort_values(tcol)
#             idx = df[tcol]

#         series = pd.to_numeric(df[vcol], errors="coerce").fillna(0.0)
#         if len(series) < 6:
#             return {"note": "Not enough history for ARIMA (need ~6+ points)."}

#         model = ARIMA(series, order=(1, 1, 1))
#         fitted = model.fit()
#         fc = fitted.forecast(steps=horizon)

#         # build periods by extending last known period
#         last_period = list(idx)[-1]
#         if hasattr(last_period, "to_period"):
#             base = pd.Period(last_period, freq='M') if hasattr(last_period, "freqstr") else None
#         else:
#             base = None

#         forecast_points = []
#         for i, val in enumerate(fc, start=1):
#             label = None
#             if isinstance(last_period, pd.Timestamp):
#                 label = (last_period + pd.DateOffset(months=i)).strftime("%Y-%m")
#             else:
#                 label = f"T+{i}"
#             forecast_points.append({"period": label, "value": float(val)})

#         return {
#             "horizon": horizon,
#             "time_col": tcol,
#             "value_col": vcol,
#             "points": forecast_points
#         }
#     except Exception as e:
#         logging.error(f"[ARIMA ERROR] {e}")
#         return {"note": f"ARIMA failed: {e}"}


import re

def extract_horizon_from_prompt(prompt: str, default: int = 3) -> int:
    """
    Extracts forecast horizon (in months) from user prompt text.
    Example: "next 6 months" -> 6
    If nothing found, returns default.
    """
    if not prompt:
        return default

    # Look for "next 6 months" or "for 12 months"
    match = re.search(r'(\d+)\s*(month|months)', prompt.lower())
    if match:
        return int(match.group(1))

    return default



def forecast_arima(rows: List[Dict[str, Any]],
                    horizon: Optional[int] = None,
                      prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:

    """
    Fit simple ARIMA(1,1,1) and forecast `horizon` future points.
    If horizon is not passed, it will be auto-detected from user prompt.
    Default horizon = 3.
    """
    if ARIMA is None:
        return {"note": "statsmodels not installed; cannot run ARIMA."}

    if not rows:
        return {"note": "No data to forecast."}

    # 🔹 Horizon logic
    if horizon is None:
        horizon = extract_horizon_from_prompt(prompt, default=3)

    tcol, vcol = _detect_time_and_value_columns(rows)
    if not tcol or not vcol:
        return {"note": f"Unable to detect time/value columns. Found time={tcol}, value={vcol}."}

    try:
        df = pd.DataFrame(rows)
        try:
            df[tcol] = pd.to_datetime(df[tcol])
            df = df.sort_values(tcol)
            idx = df[tcol]
        except Exception:
            df = df.sort_values(tcol)
            idx = df[tcol]

        series = pd.to_numeric(df[vcol], errors="coerce").fillna(0.0)
        if len(series) < 6:
            return {"note": "Not enough history for ARIMA (need ~6+ points)."}

        model = ARIMA(series, order=(1, 1, 1))
        fitted = model.fit()
        fc = fitted.forecast(steps=horizon)

        last_period = list(idx)[-1]
        forecast_points = []
        for i, val in enumerate(fc, start=1):
            if isinstance(last_period, pd.Timestamp):
                label = (last_period + pd.DateOffset(months=i)).strftime("%Y-%m")
            else:
                label = f"T+{i}"
            forecast_points.append({"period": label, "value": float(val)})

        return {
            "horizon": horizon,
            "time_col": tcol,
            "value_col": vcol,
            "points": forecast_points
        }
    except Exception as e:
        logging.error(f"[ARIMA ERROR] {e}")
        return {"note": f"ARIMA failed: {e}"}
