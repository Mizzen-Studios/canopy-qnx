"""HOST SIM imitation logs. Scripted teacher, not a safety controller."""
import json
import random
from pathlib import Path

SOURCE = 'HOST SIM synthetic kinematic demonstration; NOT QNX'
FEATURES = ['obstacle_cm', 'speed_cms', 'heading_error_mdeg']
ACTIONS = [(0, 0), (4, 0), (12, 0), (8, -10), (8, 10)]
SCENARIOS = ('straight', 'left-bend', 'right-bend')
TRAIN_SEEDS = tuple(range(8))
HELDOUT_SEEDS = tuple(range(100, 104))


def teacher(distance, speed, heading):
    """Simple demonstrator labels; learned inference does not call this."""
    if distance < 1200:
        return 0
    if distance < 3000:
        return 1
    if heading < -5000:
        return 3
    if heading > 5000:
        return 4
    return 2


def generate():
    rows = []
    # Allocate complete seeds and all their scenario traces before sampling.
    for split, seeds in [('train', TRAIN_SEEDS), ('heldout', HELDOUT_SEEDS)]:
        for scenario_index, scenario in enumerate(SCENARIOS):
            for seed in seeds:
                rng = random.Random(seed * 31 + scenario_index)
                distance = rng.randrange(4000, 10000)
                speed = rng.randrange(0, 2001)
                for step in range(32):
                    if step % 8 == 0:
                        distance = rng.randrange(200, 10001)
                    heading = rng.randrange(-14000, 14001) + (scenario_index - 1) * 3000
                    features = [max(0, distance), speed, heading]
                    label = teacher(*features)
                    rows.append(dict(source=SOURCE, split=split,
                                     trace=f'{scenario}/seed-{seed}', scenario=scenario,
                                     seed=seed, time_ms=step * 100, features=features,
                                     action=label))
                    speed += max(-80, min(80, ACTIONS[label][0] * 100 - speed))
                    distance -= speed // 10
    return rows


if __name__ == '__main__':
    Path(__file__).with_name('sim_logs.jsonl').write_text(
        ''.join(json.dumps(r, sort_keys=True) + chr(10) for r in generate()))
