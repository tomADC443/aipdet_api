import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.report.service import get_monthly_average_pivot, analyze_growth_rate, analyze_seasonal_patterns_weekly


@pytest.fixture
def sample_df():
    """Create a sample DataFrame with test data"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
    ndvi_scores = np.random.uniform(30, 70, size=len(dates))
    return pd.DataFrame({
        'capture_date': dates,
        'ndvi_score': ndvi_scores
    })

# Tests for get_monthly_average_pivot


def test_get_monthly_average_pivot_basic(sample_df):
    """Test basic functionality of get_monthly_average_pivot"""
    result = get_monthly_average_pivot(sample_df)

    assert isinstance(result, dict)
    assert 'month' in result
    assert 'values' in result
    assert len(result['month']) == len(result['values'])
    assert all(isinstance(m, str) for m in result['month'])
    assert all(isinstance(v, float) for v in result['values'])


def test_get_monthly_average_pivot_values():
    """Test that monthly averages are calculated correctly"""
    test_df = pd.DataFrame({
        'capture_date': pd.to_datetime([
            datetime(2024, 1, 15),
            datetime(2024, 1, 20),
            datetime(2024, 2, 15)
        ]),
        'ndvi_score': [10.0, 20.0, 30.0]
    })

    result = get_monthly_average_pivot(test_df)

    assert result['month'] == ['Jan', 'Feb']
    assert result['values'] == [15.0, 30.0]


def test_get_monthly_average_pivot_empty_df():
    """Test behavior with empty DataFrame"""
    empty_df = pd.DataFrame(columns=['capture_date', 'ndvi_score'])
    result = get_monthly_average_pivot(empty_df)

    assert isinstance(result, dict)
    assert result['month'] == []
    assert result['values'] == []

# Tests for analyze_growth_rate


def test_analyze_growth_rate_basic(sample_df):
    """Test basic functionality of analyze_growth_rate"""
    result = analyze_growth_rate(sample_df)

    assert isinstance(result, dict)
    assert 'weekly_changes' in result
    assert 'max_increase' in result
    assert 'max_decrease' in result

    assert 'weeks' in result['weekly_changes']
    assert 'values' in result['weekly_changes']

    for key in ['max_increase', 'max_decrease']:
        assert 'week' in result[key]
        assert 'week_description' in result[key]
        assert 'change' in result[key]
        assert 'change_percentage' in result[key]


def test_analyze_growth_rate_specific_values():
    """Test growth rate calculations with specific known values"""
    test_df = pd.DataFrame({
        'capture_date': pd.to_datetime([
            datetime(2024, 1, 1),  # Week 1
            datetime(2024, 1, 8),  # Week 2
            datetime(2024, 1, 15),  # Week 3
        ]),
        'ndvi_score': [10.0, 20.0, 15.0]
    })

    result = analyze_growth_rate(test_df)

    assert float(result['max_increase']['change']) == pytest.approx(10.0)
    assert float(result['max_decrease']['change']) == pytest.approx(-5.0)


def test_analyze_growth_rate_single_week():
    """Test behavior with only one week of data"""
    test_df = pd.DataFrame({
        'capture_date': pd.to_datetime([datetime(2024, 1, 1)]),
        'ndvi_score': [10.0]
    })

    result = analyze_growth_rate(test_df)
    assert result['weekly_changes']['weeks'] == [1]
    assert result['weekly_changes']['values'] == [None]
    assert result['max_increase']['change'] == "0.00"
    assert result['max_decrease']['change'] == "0.00"

# Tests for analyze_seasonal_patterns_weekly


def test_analyze_seasonal_patterns_basic(sample_df):
    """Test basic functionality of analyze_seasonal_patterns_weekly"""
    result = analyze_seasonal_patterns_weekly(sample_df)

    assert isinstance(result, list)
    if len(result) > 0:
        for season in result:
            assert 'season_start_week' in season
            assert 'season_end_week' in season
            assert 'season_start_description' in season
            assert 'season_end_description' in season


def test_analyze_seasonal_patterns_specific_pattern():
    """Test seasonal pattern detection with specific pattern"""
    dates = pd.date_range(start='2024-01-01', periods=52, freq='W')
    ndvi_scores = [70 if 20 <= i <= 30 else 30 for i in range(52)]

    test_df = pd.DataFrame({
        'capture_date': dates,
        'ndvi_score': ndvi_scores
    })

    result = analyze_seasonal_patterns_weekly(test_df)

    assert len(result) > 0
    found_season = False
    for season in result:
        if 20 <= season['season_start_week'] <= 30:
            found_season = True
            break
    assert found_season


def test_analyze_seasonal_patterns_empty_df():
    """Test behavior with empty DataFrame"""
    empty_df = pd.DataFrame(columns=['capture_date', 'ndvi_score'])
    result = analyze_seasonal_patterns_weekly(empty_df)
    assert isinstance(result, list)
    assert len(result) == 0


def test_analyze_seasonal_patterns_short_period():
    """Test behavior with less than 6 weeks of data"""
    dates = pd.date_range(start='2024-01-01', periods=5, freq='W')
    ndvi_scores = [70, 75, 80, 85, 90]

    test_df = pd.DataFrame({
        'capture_date': dates,
        'ndvi_score': ndvi_scores
    })

    result = analyze_seasonal_patterns_weekly(test_df)
    assert isinstance(result, list)
    assert len(result) == 0
