import aprel
import numpy as np
from gymnasium_envs import make_env
from aprel.querying.value_iteration import ValueIteration
from collections import defaultdict
import osmnx as ox
        
class APReLWrapper:
    def __init__(self, method='rl', acquisition='mutual_information', seed=0, num_trajectories=100):
        # Configure settings based on method name
        self.method = method
        self.acquisition = acquisition
        self.seed = seed
        self.num_trajectories = num_trajectories
        
        # Set query optimization parameters based on method
        if method == 'rl':
            self.query_optim = 'querygen'
            self.optimize_env = False
            self.counterfactual = False
        elif method == 'counterfactual':
            self.query_optim = 'querygen'
            self.optimize_env = False
            self.counterfactual = True
        elif method == 'envopt-rl':
            self.query_optim = 'querygen'
            self.optimize_env = True
            self.counterfactual = False
        elif method == 'envopt-counterfactual':
            self.query_optim = 'querygen'
            self.optimize_env = True
            self.counterfactual = True
        elif method == 'fixed':
            self.query_optim = 'discrete_trajectory_set'
            self.optimize_env = False
            self.counterfactual = False
        else:
            raise ValueError(f"Unknown method: {method}. Valid methods: 'rl', 'counterfactual', 'envopt-rl', 'envopt-counterfactual', 'fixed'")
        
        self.gym_env = make_env("StreetNav-v0", place="boulder")
        self.env = aprel.Environment(self.gym_env, self.gym_env.feature_func)
        
        # Initialize trajectory set based on query optimization method
        if self.query_optim == 'discrete_trajectory_set':
            trajectory_set = aprel.generate_trajectories_randomly(self.env, random_start_state=True,
                                                            num_trajectories=self.num_trajectories,
                                                            max_episode_length=100,
                                                            file_name='StreetNav-v0', restore=False,
                                                            headless=True, seed=self.seed)
        else:
            trajectory_set = aprel.generate_trajectories_randomly(self.env, random_start_state=False,
                                                            num_trajectories=2,
                                                            max_episode_length=100,
                                                            file_name='StreetNav-v0', restore=False,
                                                            headless=True, seed=self.seed)

        self.query = aprel.PreferenceQuery(trajectory_set[:2])
        self.trajectory_set = trajectory_set
        
        # Initialize query optimizer based on method
        self._initialize_query_optimizer()
    
    def _initialize_query_optimizer(self):
        """Initialize the appropriate query optimizer based on the method"""
        if self.query_optim == 'discrete_trajectory_set':
            self.query_optimizer = aprel.QueryOptimizerDiscreteTrajectorySet(self.trajectory_set)
        elif self.query_optim == 'querygen':
            self.query_optimizer = aprel.QueryOptimizerGen(
                self.env, self.env.features, horizon=self.env.env.horizon, seed=self.seed,
                optimize_env_params=self.optimize_env, counterfactual=self.counterfactual
            )
        else:
            # Default to combinatorial for other methods
            self.query_optimizer = aprel.QueryOptimizerCombinatorial(self.env, horizon=10)

    def optimize_query(self, belief):
        """
        returns the APReL query object and processed routes
        """
        # Set batch optimization method based on query optimization type
        if self.query_optim == 'discrete_trajectory_set':
            batch_optim_method = 'dpp'
        else:
            batch_optim_method = 'exhaustive_search'
            
        queries, _ = self.query_optimizer.optimize(
            self.acquisition, belief, self.query,
            batch_size=1, batch_optimization_method=batch_optim_method,
            reduced_size=200, gamma=1, distance=aprel.default_query_distance,
            query_optim=self.query_optim
        )
        
        # Return the APReL query object which contains the trajectories
        return queries[0]
    
    
    
# Default wrapper instance
aprel_wrapper = APReLWrapper(method="envopt-counterfactual")
        
        
        