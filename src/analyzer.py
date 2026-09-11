import pandas as pd
import random

AGE_GROUPS = ['0-18', '19-40', '41-60', '61-80', '81-100', '101+', 'Unknown']


def assign_age_group(age_str):
    """Assigns an age string (or 'Unknown') to an age group bucket."""
    try:
        age = int(str(age_str))
        if 0 <= age <= 18:   return '0-18'
        elif 19 <= age <= 40: return '19-40'
        elif 41 <= age <= 60: return '41-60'
        elif 61 <= age <= 80: return '61-80'
        elif 81 <= age <= 100: return '81-100'
        else: return '101+'
    except (ValueError, TypeError):
        return 'Unknown'


def calculate_statistics(df, total_pages=0, relevant_pages=0):
    """
    Calculates comprehensive (and completely unnecessary) statistics
    from the final DataFrame.
    
    Returns a dict of stats.
    """
    if df is None or df.empty:
        return None

    stats = {}
    stats['total_people'] = len(df)
    stats['total_pages'] = total_pages
    stats['relevant_pages'] = relevant_pages

    # Work with numeric ages
    numeric_df = df[df['Age'] != 'Unknown'].copy()
    numeric_df['Age_Int'] = pd.to_numeric(numeric_df['Age'], errors='coerce').dropna()
    numeric_df = numeric_df.dropna(subset=['Age_Int'])

    if not numeric_df.empty:
        stats['average_age'] = round(numeric_df['Age_Int'].mean(), 1)
        stats['median_age'] = round(numeric_df['Age_Int'].median(), 1)
        stats['youngest'] = int(numeric_df['Age_Int'].min())
        stats['oldest'] = int(numeric_df['Age_Int'].max())
        stats['above_80'] = len(numeric_df[numeric_df['Age_Int'] > 80])
        stats['below_60'] = len(numeric_df[numeric_df['Age_Int'] < 60])
        stats['pct_above_80'] = round((stats['above_80'] / len(df)) * 100, 1)
    else:
        stats['average_age'] = 'N/A'
        stats['median_age'] = 'N/A'
        stats['youngest'] = 'N/A'
        stats['oldest'] = 'N/A'
        stats['above_80'] = 0
        stats['below_60'] = 0
        stats['pct_above_80'] = 0

    stats['unknown_age_count'] = len(df[df['Age'] == 'Unknown'])

    # Alphabetical
    sorted_df = df.sort_values(by='Name', key=lambda c: c.str.lower())
    stats['first_alpha'] = sorted_df.iloc[0]['Name'] if not sorted_df.empty else 'N/A'
    stats['last_alpha'] = sorted_df.iloc[-1]['Name'] if not sorted_df.empty else 'N/A'

    # Age group stats
    df = df.copy()
    df['Age_Group'] = df['Age'].apply(assign_age_group)

    group_counts = df['Age_Group'].value_counts()
    known_groups = {k: v for k, v in group_counts.items() if k != 'Unknown'}

    if known_groups:
        max_count = max(known_groups.values())
        top_groups = [g for g, c in known_groups.items() if c == max_count]
        if len(top_groups) > 1:
            stats['most_common_group'] = ' & '.join(top_groups) + ' (Tie)'
        else:
            stats['most_common_group'] = top_groups[0]
        stats['most_common_group_count'] = max_count
        stats['largest_group_pct'] = round((max_count / len(df)) * 100, 1)
    else:
        stats['most_common_group'] = 'N/A'
        stats['most_common_group_count'] = 0
        stats['largest_group_pct'] = 0

    # Notice type breakdown
    if 'Notice_Type' in df.columns:
        stats['most_common_notice'] = df['Notice_Type'].mode().iloc[0] if not df.empty else 'N/A'
    else:
        stats['most_common_notice'] = 'N/A'

    # Page-wise entry count
    if 'Page' in df.columns:
        page_counts = df['Page'].value_counts().to_dict()
        stats['page_breakdown'] = page_counts
        if page_counts:
            stats['busiest_page'] = max(page_counts, key=page_counts.get)
            stats['busiest_page_count'] = page_counts[stats['busiest_page']]
        else:
            stats['busiest_page'] = 'N/A'
            stats['busiest_page_count'] = 0
    else:
        stats['page_breakdown'] = {}
        stats['busiest_page'] = 'N/A'
        stats['busiest_page_count'] = 0

    return stats


def generate_useless_insight(stats):
    """Generates a context-aware humorous insight from the actual stats."""
    if not stats:
        return "We found nothing. The analysis was even more useless than expected."

    templates = [
        f"Page {stats.get('busiest_page', '?')} contained {stats.get('busiest_page_count', '?')} people. "
        f"We scanned {stats.get('total_pages', '?')} pages to discover that.",

        f"The '{stats.get('most_common_group', 'unknown')}' age group had the highest representation. "
        f"This information will probably change nothing in your life.",

        f"{stats['total_people']} people were analyzed. Nobody asked us to do this.",

        f"The average age was {stats.get('average_age', '?')}. You are now unnecessarily informed.",

        f"We scanned {stats.get('total_pages', '?')} pages and extracted {stats['total_people']} entries. "
        f"The ratio of effort to usefulness is approximately infinite.",

        f"Alphabetically, we went from {stats.get('first_alpha', '?')} to {stats.get('last_alpha', '?')}. "
        f"A journey no one requested.",

        f"{stats.get('pct_above_80', 0)}% of detected individuals were above 80. "
        f"We have quantified this for absolutely no reason.",
    ]

    return random.choice(templates)


def calculate_uselessness_score(df, total_pages=1):
    """
    Calculates a deterministic, completely made-up Uselessness Score.
    Formula: pages_scanned * 3 + entries * 2 + stats_count
    Capped at 99.
    """
    if df is None or df.empty:
        return 50
    pages_score = min(total_pages * 3, 45)
    entries_score = min(len(df) * 2, 40)
    stats_score = 10  # We always calculate ~10+ stats
    return min(99, pages_score + entries_score + stats_score)
