import aprel
import numpy as np
from gymnasium_envs import make_env
from aprel.querying.value_iteration import ValueIteration
from collections import defaultdict
import osmnx as ox
        
class APReLWrapper:
    def __init__(self):
        self.gym_env = make_env("StreetNav-v0", place="boulder")
        self.env = aprel.Environment(self.gym_env, self.gym_env.feature_func)
        trajectory_set = aprel.generate_trajectories_randomly(self.env, random_start_state=False,
                                                        num_trajectories=2,
                                                        max_episode_length=100,
                                                        file_name='StreetNav-v0', restore=False,
                                                        headless=True)


        self.query = aprel.PreferenceQuery(trajectory_set[:2])
        self.query_optimizer = aprel.QueryOptimizerGen(self.env, self.env.features, horizon=self.env.env.horizon, seed=0)

    def optimize_query(self, belief):
        """
        returns the APReL query object and processed routes
        """
        queries, _ = self.query_optimizer.optimize(
            "mutual_information", belief, self.query,
            batch_size=1, batch_optimization_method="exhaustive_search",
            reduced_size=200, gamma=1, distance=aprel.default_query_distance,
            query_optim="querygen"
        )
        
        # Return the APReL query object which contains the trajectories
        return queries[0]
    
    
aprel_wrapper = APReLWrapper()
        
        
        