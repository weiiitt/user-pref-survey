import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import sys
sys.path.append('../')
from scripts.tree_node import NewTreeNode
from scripts.tree_analysis import get_estimated_rewards, TABLETOP_TRUE_WEIGHTS, TABLETOP_FEATURE_BOUNDS

def create_survey_plots(test_type: str, user_choices: list[list[list[int]]], condition_labels: list[str], conditions: list[int] = [0, 1, 2]):
    """
    Create plots for the survey data.
    Args:
        test_type: str, the type of test
        user_choices: list[list[list[int]]], the user choices for each condition (user_choice[condition][user][choice])
        conditions: list[int], the conditions to plot
    Returns:
        correlations: dict, the correlations for each condition
    """
    if len(user_choices) != len(conditions):
        raise ValueError("mismatched length between user_choices and conditions")
    
    if len(condition_labels) != len(conditions):
        raise ValueError("mismatched length between condition_labels and conditions")
    # Check if all conditions have same number of users
    num_users = len(user_choices[0])
    for condition_choices in user_choices:
        if len(condition_choices) != num_users:
            raise ValueError(f"All conditions must have same number of users. Found {num_users} vs {len(condition_choices)}")
    
    condition_objects = []
    for condition in conditions:
        pkl_path = f'../../server/assets/user_study/{test_type}-v{condition}/query_tree_{test_type}-v{condition}.pkl'
    
        with open(pkl_path, 'rb') as f:
            obj = pickle.load(f)
        condition_objects.append(obj)
    
    correlations = {
        "condition": condition_labels,
        "correlations": [],
        "most_common_paths": [],
        "num_unique_paths": []
    }
    for condition, condition_object in enumerate(condition_objects):
        # Compute most common truncated (first 5) paths per condition and collect final nodes in a single pass
        path_counts = {}
        final_nodes = []
        for user in user_choices[condition]:
            if len(user) < 5:
                print("! some users have less than 5 choices")
                exit()
            path_str = "".join(str(choice) for choice in user[:5])
            path_counts[path_str] = path_counts.get(path_str, 0) + 1
            final_node = condition_object
            for idx, choice in enumerate(user):
                if idx > 4:
                    print("! some users have extra choices")
                    break
                final_node = final_node.children[choice]
            final_nodes.append(final_node)
        if path_counts:
            max_count = max(path_counts.values())
            most_common_list = [p for p, cnt in path_counts.items() if cnt == max_count]
        else:
            most_common_list = []
        correlations["most_common_paths"].append(most_common_list)
        correlations["num_unique_paths"].append(len(path_counts))
        r_values = []
        for final_node in final_nodes:
            r, pvalue = get_estimated_rewards(final_node, TABLETOP_TRUE_WEIGHTS, TABLETOP_FEATURE_BOUNDS)
            r_values.append(r)
        correlations["correlations"].append(r_values)
    
    correlations = pd.DataFrame(correlations)
    
    sns.set_theme(style="whitegrid")
    ax = sns.boxplot(
        x='condition',
        y='correlations',
        data=correlations.explode('correlations'),
        palette='Set2'
    )
    ax.set_title(f'Distribution of Correlations by Condition ({test_type})')
    ax.set_xlabel('Condition')
    ax.set_ylabel('Correlation')
    plt.tight_layout()
    plt.savefig(f'correlation_boxplot_{test_type}.png')
    plt.close()
    
    


        
        
        
    
    