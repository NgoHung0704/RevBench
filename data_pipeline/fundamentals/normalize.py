"""Clean a metric's EDGAR facts into a comparable series (docs/REVISIT.md R4).

EDGAR mixes 3-month (10-Q), full-year (10-K), and sometimes year-to-date values
for the same concept, and repeats each period across later filings as restated
comparatives. Comparing those naively produced the "unusual revenue spike" the
Fundamentals Agent flagged. This keeps one clean quarterly series (falling back
to annual) and compares like-with-like (year-over-year).
"""

import pandas as pd

QUARTERLY_DAYS = (75, 100)  # a fiscal quarter is ~13 weeks
ANNUAL_DAYS = (350, 380)


def _period_days(facts: pd.DataFrame) -> pd.Series:
    start = pd.to_datetime(facts["period_start"])
    end = pd.to_datetime(facts["period_end"])
    return (end - start).dt.days


def quarterly_series(facts_for_metric: pd.DataFrame) -> pd.DataFrame:
    """One row per fiscal period for a single metric, oldest first, with a
    year-over-year change. Prefers 3-month periods; falls back to annual when a
    metric is only reported yearly. Returns columns: period_end, value, yoy,
    period_type. Empty in -> empty out.
    """
    if facts_for_metric.empty:
        return pd.DataFrame(columns=["period_end", "value", "yoy", "period_type"])

    df = facts_for_metric.copy()
    df["days"] = _period_days(df)

    period_type = "quarterly"
    series = df[df["days"].between(*QUARTERLY_DAYS)]
    if series.empty:
        period_type = "annual"
        series = df[df["days"].between(*ANNUAL_DAYS)]
    if series.empty:
        return pd.DataFrame(columns=["period_end", "value", "yoy", "period_type"])

    # the same period is restated across filings — keep the latest-filed value
    series = (
        series.sort_values("filed")
        .drop_duplicates("period_end", keep="last")
        .sort_values("period_end")
        .reset_index(drop=True)
    )
    series["yoy"] = _year_over_year(series)
    series["period_type"] = period_type
    return series[["period_end", "value", "yoy", "period_type"]]


def _year_over_year(series: pd.DataFrame) -> list[float]:
    """value / value ~365 days earlier - 1, matched by date.

    Matching by date (not positional shift) is robust to gaps — e.g. a company
    that files Q4 only inside its annual 10-K is missing one quarterly row, so a
    positional shift would compare the wrong fiscal quarters.
    """
    ends = pd.to_datetime(series["period_end"])
    values = series["value"].to_numpy()
    out: list[float] = []
    for i, end in enumerate(ends):
        target = end - pd.Timedelta(days=365)
        diffs = (ends - target).abs()
        j = diffs.idxmin()
        if j < i and diffs.iloc[j] <= pd.Timedelta(days=45) and values[j] != 0:
            out.append(values[i] / values[j] - 1)
        else:
            out.append(float("nan"))
    return out
