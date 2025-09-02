from dataclasses import dataclass, field
from typing import Optional, Union, Dict

@dataclass
class NewTreeNode:
    # Structure
    depth: int
    response: Optional[int]                # 0, 1, or None at root
    path: str                              # string like '', '0', '01', ...
    # Visualization / assets
    trajectory_A_file: Optional[str] = None
    trajectory_B_file: Optional[str] = None
    # Environment details (kept as plain Python types only)
    env_params: Optional[Union[dict, list, tuple, float, int, str]] = None
    # Optional compact summary of belief (no APReL objects)
    belief_summary: Optional[dict] = None
    # Optional compact summary of query (kept minimal/plain types)
    query_summary: Optional[dict] = None
    # Children map {0: NewTreeNode, 1: NewTreeNode}
    children: Dict[int, "NewTreeNode"] = field(default_factory=dict)