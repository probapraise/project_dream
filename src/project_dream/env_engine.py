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


def apply_policy_transition(status: str, reports: int, severity: int, appeal: bool) -> tuple[str, dict]:
    if appeal and status in {"hidden", "locked", "ghost"}:
        rollback = {
            "hidden": "visible",
            "locked": "hidden",
            "ghost": "locked",
        }
        next_status = rollback[status]
        return next_status, {
            "action_type": "APPEAL",
            "prev_status": status,
            "next_status": next_status,
            "reason_rule_id": "RULE-PLZ-SAN-02",
        }

    if status == "visible" and reports >= 10:
        return "hidden", {
            "action_type": "HIDE_PREVIEW",
            "prev_status": status,
            "next_status": "hidden",
            "reason_rule_id": "RULE-PLZ-MOD-01",
        }
    if status == "hidden" and reports >= 20:
        return "locked", {
            "action_type": "LOCK_THREAD",
            "prev_status": status,
            "next_status": "locked",
            "reason_rule_id": "RULE-PLZ-MOD-02",
        }
    if status == "locked" and (reports >= 25 or severity >= 2):
        return "ghost", {
            "action_type": "GHOST_THREAD",
            "prev_status": status,
            "next_status": "ghost",
            "reason_rule_id": "RULE-PLZ-MOD-03",
        }
    if status == "ghost" and (reports >= 30 or severity >= 3):
        return "sanctioned", {
            "action_type": "SANCTION_USER",
            "prev_status": status,
            "next_status": "sanctioned",
            "reason_rule_id": "RULE-PLZ-SAN-01",
        }

    return status, {
        "action_type": "NO_OP",
        "prev_status": status,
        "next_status": status,
        "reason_rule_id": "RULE-PLZ-UI-01",
    }
