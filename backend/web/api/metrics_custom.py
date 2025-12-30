from prometheus_client import Counter

experiment_marker_total = Counter(
    "experiment_marker_total",
    "Manual markers for experiments",
    ["name"],
)
