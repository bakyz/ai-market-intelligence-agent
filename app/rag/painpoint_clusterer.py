from collections import defaultdict
from typing import List


class PainPointClusterer:
    def cluster(self, pain_points: List[str]):

        clusters = defaultdict(list)

        for p in pain_points:
            key = p.split()[0]
            clusters[key].append(p)

        return dict(clusters)
