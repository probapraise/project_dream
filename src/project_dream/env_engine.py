def compute_score(
    up: int,
    comments: int,
    views: int,
    preserve: int,
    reports: int,
    trust: int,
    urgent: int = 0,
) -> float:
    w1, w2, w3, w4, w5, w6 = 1.0, 1.3, 0.2, 3.0, 1.8, 1.1
    return (up * w1) + (comments * w2) + (views * w3) + (preserve * w4) - (reports * w5) + (trust * w6) + urgent


def apply_report_threshold(status: str, reports: int, threshold: int) -> str:
    if reports >= threshold:
        return "hidden"
    return status
