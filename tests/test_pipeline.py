import pandas as pd
import pytest
from pathlib import Path              

DATA_DIR = Path(__file__).parent.parent / "data"  

def test_boj_rate_has_variation():
    """
    WHY this test exists: we hit a real bug where BOJ rate 
    was flat at 0.3 for all 120 rows due to using the wrong 
    FRED series ID. This test would have caught that bug 
    automatically, before it silently corrupted downstream 
    correlations.
    """
    boj_rate_df = pd.read_csv(DATA_DIR / "raw" / "boj_rate_raw.csv")
    
    unique_values = boj_rate_df['boj_rate_pct'].nunique()
    
    assert unique_values > 1, (
        f"BOJ rate has only {unique_values} unique value(s) — "
        f"likely the same flat-series bug we found earlier"
    )



def test_annual_master_has_one_row_per_year():
    """
    WHY this test exists: The annual dataset is the foundation for most
    of the project's macroeconomic correlations. If a year is duplicated
    or silently dropped during aggregation/merging, the analysis can
    produce incorrect results without obvious errors.
    """
    annual = pd.read_csv(DATA_DIR / "processed" / "annual_enriched.csv")
    
    expected_years = list(range(2014, 2024))
    
    # Check 1: no duplicate years
    assert not annual["year"].duplicated().any(), \
        "Annual master contains duplicate years"
    
    # Check 2: no missing years
    actual_years = sorted(annual["year"].unique())
    assert actual_years == expected_years, \
        f"Expected years {expected_years}, but found {actual_years}"



def test_nikkei_annual_average_is_correct():
    """
    WHY this test exists: verifies the pipeline's annual average 
    wasn't accidentally computed from the wrong column, wrong date 
    range, or using .first()/.last() instead of .mean(). We 
    independently recalculate one year's average directly from 
    raw daily data and compare it to the pipeline's output.
    """
    nikkei_daily = pd.read_csv(DATA_DIR / "raw" / "nikkei_raw.csv")
    nikkei_daily['Date'] = pd.to_datetime(nikkei_daily['Date'])
    
    # Independently recalculate 2020's average, from scratch
    year_2020 = nikkei_daily[nikkei_daily['Date'].dt.year == 2020]
    independent_avg = year_2020['Close'].mean()
    
    # Load the pipeline's actual output for comparison
    annual = pd.read_csv(DATA_DIR / "processed"/ "annual_enriched.csv")
    pipeline_avg = annual.loc[annual['year'] == 2020, 
                               'nikkei_avg_close'].values[0]
    
    # WHY pytest.approx() instead of ==:
    # Handles tiny floating-point differences from independent 
    # calculation paths, while still catching REAL bugs (like 
    # using .first() instead of .mean(), which would produce a 
    # wildly different number, not just a rounding difference)
    
    assert pipeline_avg == pytest.approx(independent_avg, rel=1e-6), (
        f"Pipeline avg ({pipeline_avg}) doesn't match independent "
        f"calculation ({independent_avg})"
    )