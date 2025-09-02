import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pickle
from scripts.tree_node import NewTreeNode
import numpy as np
from scipy.stats import pearsonr

tabletop_weights = np.array([-1.0, -1.0, -5.0, -2.0])
grass_street_nav_weights = np.array([-2.0, -0.1, -0.1, -5.0, -0.1])

TABLETOP_FEATURE_BOUNDS = [(0, 4) for _ in range(4)]
TABLETOP_TRUE_WEIGHTS = tabletop_weights / np.linalg.norm(tabletop_weights)

GRASS_STREET_NAV_FEATURE_BOUNDS = [(-1, 1) for _ in range(5)]
GRASS_STREET_NAV_TRUE_WEIGHTS = grass_street_nav_weights / np.linalg.norm(grass_street_nav_weights)

def generate_feature_grid(feature_bounds, bins_per_dim=10):
    """
    Generate a uniform grid in feature space.
    
    Args:
        feature_bounds: List of (min, max) tuples for each feature dimension.
        bins_per_dim: Number of grid points per feature dimension.
    
    Returns:
        grid_x: (N, d) array of feature vectors on the grid.
    """
    grid_axes = [np.linspace(low, high, bins_per_dim) for (low, high) in feature_bounds]
    mesh = np.meshgrid(*grid_axes)
    grid_x = np.stack([m.ravel() for m in mesh], axis=-1)
    return grid_x

def get_estimated_rewards(node, true_weights, feature_bounds):
    grid_x = generate_feature_grid(feature_bounds, bins_per_dim=5)

    true_rewards = grid_x @ true_weights
    estimated_rewards = grid_x @ node.belief_summary['weights_mean']

    r, pvalue = pearsonr(true_rewards, estimated_rewards)
    # print(f"Pearson correlation coefficient: {r} (p-value: {pvalue})")
    # print(node.belief_summary['weights_mean'])
    return r, pvalue

def analyze_tree(root_node, true_weights):
    """Uses true weights to analyze the query tree."""
    print("True weights:", true_weights)

    current_node = root_node
    while current_node.children:
        print(f"\nCurrent path: {current_node.get_path()} | Depth: {current_node.depth}")
        features_matrix = current_node.query.slate.features_matrix
        rewards = features_matrix @ true_weights
        if rewards[0] > rewards[1]:
            response = 0
        else:
            response = 1

        get_estimated_rewards(current_node, true_weights)
        if response in current_node.children:
            current_node = current_node.children[response]
        else:
            print("Invalid response. Ending session.")
            break

    print(current_node.children)
    print("\nReached a leaf node. Analyzing final node...")
    get_estimated_rewards(current_node, true_weights)