import pandas as pd
from typing import Dict, List, Union

from datetime import datetime
import calendar


def get_monthly_average_pivot(df: pd.DataFrame) -> Dict[str, List[Union[str, float]]]:
    if df.empty:
        return {'month': [], 'values': []}

    df['month'] = pd.to_datetime(df['capture_date']).dt.month
    monthly_means = df.groupby('month')['ndvi_score'].mean()
    monthly_dict = {
        'month': [calendar.month_abbr[m] for m in monthly_means.index],
        'values': [float(x) for x in monthly_means.values.tolist()]
    }
    return monthly_dict


def analyze_growth_rate(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    try:
        if df.empty:
            return {
                'weekly_changes': {'weeks': [], 'values': []},
                'max_increase': {'week': '0', 'week_description': '', 'change': '0.00', 'change_percentage': '0.0%'},
                'max_decrease': {'week': '0', 'week_description': '', 'change': '0.00', 'change_percentage': '0.0%'}
            }

        df['week'] = pd.to_datetime(df['capture_date']).dt.isocalendar().week
        weekly_means = df.groupby('week')['ndvi_score'].mean()

        if len(weekly_means) <= 1:
            return {
                'weekly_changes': {'weeks': [int(weekly_means.index[0])], 'values': [None]},
                'max_increase': {'week': '0', 'week_description': get_week_description(int(weekly_means.index[0])),
                                 'change': '0.00', 'change_percentage': '0.0%'},
                'max_decrease': {'week': '0', 'week_description': get_week_description(int(weekly_means.index[0])),
                                 'change': '0.00', 'change_percentage': '0.0%'}
            }

        changes = weekly_means.diff()
        weeks = sorted(weekly_means.index)

        changes_dict = {int(k): None if pd.isna(v) else float(v)
                        for k, v in changes.to_dict().items()}

        max_increase = float(
            changes.max() if not pd.isna(changes.max()) else 0)
        max_increase_week = int(changes.idxmax() if not pd.isna(
            changes.idxmax()) else weeks[0])
        max_decrease = float(
            changes.min() if not pd.isna(changes.min()) else 0)
        max_decrease_week = int(changes.idxmin() if not pd.isna(
            changes.idxmin()) else weeks[0])

        # Get previous week safely
        prev_week_increase = weeks[max(0, weeks.index(max_increase_week) - 1)]
        prev_week_decrease = weeks[max(0, weeks.index(max_decrease_week) - 1)]

        return {
            'weekly_changes': {
                'weeks': list(changes_dict.keys()),
                'values': list(changes_dict.values())
            },
            'max_increase': {
                'week': str(max_increase_week),
                'week_description': get_week_description(max_increase_week),
                'change': f"{max_increase:.2f}",
                'change_percentage': f"{((max_increase / weekly_means[prev_week_increase]) * 100) if max_increase != 0 and not pd.isna(weekly_means.get(prev_week_increase, None)) else 0:.1f}%"
            },
            'max_decrease': {
                'week': str(max_decrease_week),
                'week_description': get_week_description(max_decrease_week),
                'change': f"{max_decrease:.2f}",
                'change_percentage': f"{((max_decrease / weekly_means[prev_week_decrease]) * 100) if max_decrease != 0 and not pd.isna(weekly_means.get(prev_week_decrease, None)) else 0:.1f}%"
            }
        }

    except Exception as e:
        print(f"Error in analyze_growth_rate: {e}")
        return {
            'weekly_changes': {'weeks': [], 'values': []},
            'max_increase': {'week': '0', 'week_description': '', 'change': '0.00', 'change_percentage': '0.0%'},
            'max_decrease': {'week': '0', 'week_description': '', 'change': '0.00', 'change_percentage': '0.0%'}
        }


def analyze_seasonal_patterns_weekly(df: pd.DataFrame) -> List[Dict[str, Union[int, str]]]:
    if df.empty:
        print("Seasonal Pattern - No data received")
        return []

    # data prep
    df['week'] = pd.to_datetime(df['capture_date']).dt.isocalendar().week
    weekly_means = df.groupby('week')['ndvi_score'].mean()

    if len(weekly_means) < 6:  # Return early if less than 6 weeks of data
        print("Seasonal Pattern - Not enough data")
        return []

    # smoothing
    smoothed_values = weekly_means.rolling(
        window=2, center=True, min_periods=1).mean()

    # Get above/below threshold
    threshold = smoothed_values.mean()
    above_threshold = smoothed_values > threshold

    # 53 or 52 depending on the year
    last_week = last_week = int(max(weekly_means.index))

    # Find blocks
    blocks = []
    start = None

    # Add week validation before block merging (to avoid invalid blocks)
    for i in range(len(blocks)):
        if blocks[i][0] not in weekly_means.index or blocks[i][1] not in weekly_means.index:
            print(f"Skipping invalid block {blocks[i]} - missing week data")
            blocks.pop(i)
            i -= 1

    for week in sorted(above_threshold.index):
        week = int(week)
        if above_threshold[week]:
            if start is None:
                start = week
        else:
            if start is not None:
                blocks.append([start, week - 1])
                start = None

    # add last block if not ended
    if start is not None:
        blocks.append([start, max(above_threshold.index)])

    # check if blocks are 2 weeks or less apart and merge them
    i = 0
    while i < len(blocks) - 1:
        if (blocks[i+1][0] - blocks[i][1]) <= 2:
            blocks[i][1] = blocks[i+1][1]
            blocks.pop(i+1)
        else:
            i += 1

    # check if the last block is two weeks or less apart from the first block and merge them
    if len(blocks) >= 2:
        if blocks[0][0] <= 2 or (last_week - blocks[-1][1]) <= 2:
            merged = [blocks[-1][0], blocks[0][1]]
            blocks = [merged] + blocks[1:-1]

    # check if all blocks have a minimum length of 6 (otherwise remove them)
    blocks = [block for block in blocks if (
        # Case 1: Normal blocks (end >= start): Check if length is 6+ weeks
        (end := block[1]) >= (start := block[0]) and end - start + 1 >= 6
        or
        # Case 2: year-around blocks (crossing year end): Calculate total length as
        # weeks remaining in year + weeks in new year
        start > end and (
            # Handle edge case when start week > 52
            start > last_week and last_week - last_week + 1 + end >= 6
            or last_week - start + 1 + end >= 6
        )
    )]
    # Convert blocks to strings for output
    blocks_with_descriptions = []
    for block in blocks:
        blocks_with_descriptions.append({
            "season_start_week": int(block[0]),
            "season_end_week": int(block[1]),
            "season_start_description": get_week_description(block[0]),
            "season_end_description": get_week_description(block[1])
        })

    return blocks_with_descriptions


def get_week_description(week_number: int) -> str:
    # Handle special case for week 53
    if week_number == 53:
        # Check if current year has 53 weeks
        current_year = datetime.now().year
        last_day = datetime(current_year, 12, 31)
        if last_day.isocalendar()[1] != 53:
            return "Late December"  # Default for non-existent week 53

    # Get current year
    current_year = datetime.now().year

    # Get the monday of the requested week
    monday = datetime.strptime(
        f'{current_year}-W{week_number:02d}-1', '%Y-W%W-%w')

    # Get the month name
    month = monday.strftime('%B')

    # Calculate which part of the month we're in
    day_of_month = monday.day
    _, last_day = calendar.monthrange(current_year, monday.month)

    if day_of_month <= 10:
        part = "Early"
    elif day_of_month > 21:
        part = "Late"
    else:
        part = "Mid"

    return f"{part} {month}"
