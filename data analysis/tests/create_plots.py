import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import sys
import os

# Ensure the parent directory (which contains the 'scripts' package) is on sys.path,
# regardless of the current working directory when this script is executed.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)
from scripts.tree_node import NewTreeNode
from scripts.tree_analysis import (
    get_estimated_rewards,
    TABLETOP_TRUE_WEIGHTS,
    TABLETOP_FEATURE_BOUNDS,
    GRASS_STREET_NAV_TRUE_WEIGHTS,
    GRASS_STREET_NAV_FEATURE_BOUNDS,
)

import argparse
from typing import Optional, List
import ast

def create_metric_boxplots_from_csv(
    data: pd.DataFrame,
    condition_labels: List[str],
    outdir: str,
    tests: Optional[List[str]] = None,
):
    """
    Generate box plots per test_type for overall_workload and Q4–Q6 metrics
    using a survey export CSV (format like server/survey_export_pilot_1.csv).

    Args:
        data: pandas DataFrame (one row per user x condition x test_type)
        condition_labels: labels to map from numeric condition_number (sorted unique) to strings
        outdir: directory to write plot files
        tests: optional subset of test_type values to include; if None, include all present
    """
    # Load CSV
    df = data

    # Compute overall_workload = (Q1_mental_demand + (8 - Q2_success) + Q3_frustration) / 3
    # CSV columns are named: mental_demand, success_level, frustration_level
    df['overall_workload'] = (
        df['mental_demand'] + (8 - df['success_level']) + df['frustration_level']
    ) / 3.0

    # Determine tests to plot
    tests_to_plot = tests if tests is not None and len(tests) > 0 else sorted(df['test_type'].unique())

    # Map numeric conditions to provided labels (in sorted order by condition_number)
    unique_conditions = sorted(df['condition_number'].unique())
    if len(condition_labels) != len(unique_conditions):
        raise ValueError(
            f"condition_labels length {len(condition_labels)} does not match number of unique conditions {len(unique_conditions)}"
        )
    condition_map = {cond: condition_labels[idx] for idx, cond in enumerate(unique_conditions)}
    df['condition'] = df['condition_number'].map(condition_map)

    # Ensure output directory exists
    os.makedirs(outdir, exist_ok=True)

    # Configure style once
    sns.set_theme(style="whitegrid")

    # Define metrics to plot: label -> column in CSV/DF
    metrics = [
        ("Overall workload", "overall_workload"),
        ("How easy it was to choose between the trajectories", "trajectory_choice_ease"),
        ("How easy it was to tell the difference between the options", "difference_clarity"),
        ("How well preferences were learned", "preference_learning"),
    ]

    for test in tests_to_plot:
        sub = df[df['test_type'] == test]
        if sub.empty:
            continue

        for label_name, col_name in metrics:
            # Guard for missing columns
            if col_name not in sub.columns:
                continue
            
            plt.figure(figsize=(8, 6))
            ax = sns.boxplot(
                x='condition',
                y=col_name,
                hue='condition',
                data=sub,
                palette='Set2'
            )
            # Hide redundant legend when hue==x
            if ax.get_legend() is not None:
                ax.get_legend().remove()
            ax.set_title(f'{label_name} by condition ({test})', pad=20)  # Added pad parameter
            ax.set_xlabel('Condition')
            ax.set_ylabel('')
            ax.set_ylim(1, 7)
            ax.text(-0.08, 0.00, 'Not at all', transform=ax.transAxes, ha='right', va='center')
            ax.text(-0.08, 1.00, 'Extremely', transform=ax.transAxes, ha='right', va='center')
            plt.tight_layout()
            outfile = os.path.join(outdir, f'boxplot_{test}_{label_name}.png')
            plt.savefig(outfile)
            plt.close()


def _parse_labels_arg(raw: List[str]) -> List[str]:
    """
    Accept labels either as a list [A B C] via nargs or a single comma-separated string.
    """
    if len(raw) == 1 and (',' in raw[0]):
        return [s.strip() for s in raw[0].split(',') if s.strip()]
    return raw


def create_survey_plots(data: pd.DataFrame, condition_labels: List[str], outdir: str, tests: Optional[List[str]] = None):
    """
    Generate correlation box plots using PKL trees, driven by user choices from CSV.

    - Reads choices per (test_type, condition_number) from CSV
    - Loads the corresponding PKL tree for each condition
    - Traverses the first 5 choices to a final node
    - Computes estimated reward correlation for each user via get_estimated_rewards
    - Creates a seaborn box plot of correlations grouped by condition labels per test_type

    Args:
        data: pandas DataFrame (must include: test_type, condition_number, choices)
        condition_labels: labels in order of sorted unique condition_number values
        outdir: directory to write plots
        tests: optional subset of test_type values to include (e.g., ['robot_nav','tabletop'])
    """
    df = data

    tests_to_plot = tests if tests is not None and len(tests) > 0 else sorted(df['test_type'].unique())

    unique_conditions = sorted(df['condition_number'].unique())
    if len(condition_labels) != len(unique_conditions):
        raise ValueError(
            f"condition_labels length {len(condition_labels)} does not match number of unique conditions {len(unique_conditions)}"
        )
    condition_map = {cond: condition_labels[idx] for idx, cond in enumerate(unique_conditions)}

    # Resolve repo root to load PKL files reliably
    REPO_ROOT = os.path.dirname(PARENT_DIR)

    os.makedirs(outdir, exist_ok=True)
    sns.set_theme(style="whitegrid")

    for test in tests_to_plot:
        sub = df[df['test_type'] == test]
        if sub.empty:
            continue
        
        if test == "robot_nav":
            test_name = "GrassStreetNav"
            true_weights = GRASS_STREET_NAV_TRUE_WEIGHTS
            feature_bounds = GRASS_STREET_NAV_FEATURE_BOUNDS
        else:
            test_name = "TableTop"
            true_weights = TABLETOP_TRUE_WEIGHTS
            feature_bounds = TABLETOP_FEATURE_BOUNDS

        # Load trees per condition for this test_type
        trees_by_condition = {}
        for cond in unique_conditions:
            pkl_path = os.path.join(
                REPO_ROOT,
                'server', 'assets', 'user_study', f'{test_name}-v{cond}', f'query_tree_{test_name}-v{cond}.pkl'
            )
            with open(pkl_path, 'rb') as f:
                trees_by_condition[cond] = pickle.load(f)

        # Build per-user correlation rows for seaborn
        rows = []
        for _, row in sub.iterrows():
            cond = int(row['condition_number'])
            choices_str = row['choices']
            try:
                choices = ast.literal_eval(choices_str)
            except Exception:
                continue
            if not isinstance(choices, list):
                continue
            if len(choices) < 5:
                continue

            final_node = trees_by_condition[cond]
            for idx, choice in enumerate(choices):
                if idx > 4:
                    break
                try:
                    final_node = final_node.children[choice]
                except Exception:
                    final_node = None
                    break
            if final_node is None:
                continue

            r, _ = get_estimated_rewards(final_node, true_weights, feature_bounds)
            rows.append({
                'condition': condition_map[cond],
                'correlation': r,
            })

        if not rows:
            continue

        plot_df = pd.DataFrame(rows)
        plt.figure(figsize=(8, 6))
        ax = sns.boxplot(
            x='condition',
            y='correlation',
            hue='condition',
            data=plot_df,
            palette='Set2'
        )
        if ax.get_legend() is not None:
            ax.get_legend().remove()
        ax.set_title(f'Distribution of Correlations by Condition ({test_name})')
        ax.set_xlabel('Condition')
        ax.set_ylabel('Correlation')
        plt.tight_layout()
        outfile = os.path.join(outdir, f'correlation_boxplot_{test_name}.png')
        plt.savefig(outfile)
        plt.close()    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate survey metric box plots from CSV')
    parser.add_argument('--csv', required=True, help='Path to survey export CSV')
    parser.add_argument('--outdir', default='.', help='Directory to write plots')
    parser.add_argument(
        '--labels',
        required=True,
        nargs='+',
        help='Condition labels in order of sorted condition_number (e.g., Condition_A Condition_B Condition_C or a single comma-separated string)'
    )
    parser.add_argument(
        '--tests',
        nargs='+',
        default=None,
        help='Optional subset of test_type values to include (e.g., robot_nav tabletop)'
    )

    args = parser.parse_args()
    labels = _parse_labels_arg(args.labels)
    
    data = pd.read_csv(args.csv)
    
    # Filter responses based on expected choice counts and non-empty survey metrics
    survey_metrics = ['mental_demand', 'success_level', 'frustration_level', 
                     'trajectory_choice_ease', 'difference_clarity', 'preference_learning']
    
    # First filter by expected choice counts per test_type
    if 'tabletop' in data['test_type'].unique():
        tabletop_mask = (data['test_type'] == 'tabletop')
        data.loc[tabletop_mask, 'choices'] = data.loc[tabletop_mask, 'choices'].apply(
            lambda x: x if isinstance(x, str) and len(eval(x)) == 5 else np.nan
        )
    if 'robot_nav' in data['test_type'].unique():
        robot_nav_mask = (data['test_type'] == 'robot_nav')
        data.loc[robot_nav_mask, 'choices'] = data.loc[robot_nav_mask, 'choices'].apply(
            lambda x: x if isinstance(x, str) and len(eval(x)) == 6 else np.nan
        )
    data = data.dropna(subset=['choices'])
    
    # Then filter for users who completed all conditions (0,1,2) for each test_type
    # and have all survey metrics filled
    valid_users = []
    for user_id, user_data in data.groupby('user_id'):
        # Check if user has all conditions (0,1,2) for each test_type they attempted
        test_types = user_data['test_type'].unique()
        valid = True
        for test in test_types:
            if len(user_data[user_data['test_type'] == test]['condition_number'].unique()) < 3:
                valid = False
                break
        
        # Check all survey metrics are present and non-null
        if valid and not user_data[survey_metrics].isnull().any().any():
            valid_users.append(user_id)
            
    print(f"Number of valid users: {len(valid_users)}")
    
    data = data[data['user_id'].isin(valid_users)]
    
    create_metric_boxplots_from_csv(
        data=data,
        condition_labels=labels,
        outdir=args.outdir,
        tests=args.tests,
    )
    create_survey_plots(
        data=data,
        condition_labels=labels,
        outdir=args.outdir,
        tests=args.tests,
    )