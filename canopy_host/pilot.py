"""Learned HOST SIM requests; never owns or clears safestop state."""
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Request:
    speed_mps: int
    steering_deg: int


class Pilot:
    def __init__(self, model_path=None):
        path = Path(model_path) if model_path else Path(__file__).resolve().parents[1] / 'ai/pilot_model.json'
        model = json.loads(path.read_text())
        self._nodes = model['nodes']
        self._actions = model['actions']

    def request(self, obstacle_cm, speed_cms, heading_error_mdeg):
        features = (obstacle_cm, speed_cms, heading_error_mdeg)
        bounds = ((0, 10000), (0, 2000), (-20000, 20000))
        if any(type(x) is not int or not low <= x <= high
               for x, (low, high) in zip(features, bounds)):
            raise ValueError('pilot requires in-domain integer HOST SIM features')
        index = 0
        while self._nodes[index]['feature'] >= 0:
            node = self._nodes[index]
            index = node['left'] if features[node['feature']] <= node['threshold'] else node['right']
        return Request(*self._actions[self._nodes[index]['action']])
