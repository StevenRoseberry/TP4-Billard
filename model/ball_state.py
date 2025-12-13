from dataclasses import dataclass
from typing import Tuple

# Classe utile si on veut sauvegarder les parties éventuellement
@dataclass
class BallState:
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    angular_velocity: float