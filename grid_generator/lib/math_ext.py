from __future__ import division
from collections import Counter


def avg(values):
    try:
        return sum(values) / len(values)
    except:
        return None


def mode(values):
    try:
        return Counter(values).most_common(1)[0][0]  # mode
    except:
        return None
