from __future__ import annotations

from collections.abc import Iterable


_ACCOUNT_EXPOSURE_MULTIPLIER = {
    "public": 1.0,
    "alias": 0.94,
    "mask": 0.86,
}

_ACCOUNT_COST_MULTIPLIER = {
    "public": 1.0,
    "alias": 1.12,
    "mask": 1.25,
}

_ACCOUNT_THRESHOLD_OFFSET = {
    "public": 2,
    "alias": 0,
    "mask": -2,
}

_ACTION_BASE_COST = {
    "POST_COMMENT": 1.0,
    "REPORT": 0.7,
    "APPEAL": 1.4,
    "LOCK_THREAD": 3.0,
    "GHOST_THREAD": 4.0,
    "SANCTION_USER": 5.0,
}

_TAB_SCORE_MULTIPLIER = {
    "latest": 0.95,
    "weekly_hot": 1.0,
    "evidence_first": 0.98,
    "preserve_first": 1.02,
}

_STATUS_FLOOR_LEVEL = {
    "visible": 0,
    "hidden": 2,
    "locked": 3,
    "ghost": 4,
    "sanctioned": 5,
}


def _normalize_account_type(account_type: str) -> str:
    return account_type if account_type in _ACCOUNT_EXPOSURE_MULTIPLIER else "alias"


def _normalize_tab(tab: str) -> str:
    return tab if tab in _TAB_SCORE_MULTIPLIER else "weekly_hot"


def _thresholds_for(account_type: str, verified: bool) -> dict[str, int]:
    base = {
        "hidden": 10,
        "locked": 20,
        "ghost": 25,
        "sanctioned": 30,
    }
    account = _normalize_account_type(account_type)
    offset = _ACCOUNT_THRESHOLD_OFFSET[account]
    if verified:
        offset += 2
    return {key: max(1, value + offset) for key, value in base.items()}


def compute_action_cost(action_type: str, account_type: str = "public", sanction_level: int = 0) -> float:
    account = _normalize_account_type(account_type)
    base_cost = _ACTION_BASE_COST.get(action_type, 1.0)
    level = max(0, min(int(sanction_level), 5))
    sanction_multiplier = 1.0 + (level * 0.08)
    return round(base_cost * _ACCOUNT_COST_MULTIPLIER[account] * sanction_multiplier, 4)


def compute_sanction_level(reports: int, severity: int, status: str = "visible") -> int:
    report_count = max(0, int(reports))
    if report_count >= 32:
        base = 5
    elif report_count >= 26:
        base = 4
    elif report_count >= 19:
        base = 3
    elif report_count >= 12:
        base = 2
    elif report_count >= 5:
        base = 1
    else:
        base = 0

    sev = max(0, int(severity))
    if sev >= 2 and base < 4:
        base += 1

    floor = _STATUS_FLOOR_LEVEL.get(status, 0)
    return max(0, min(5, max(base, floor)))


def compute_score(
    up: int,
    comments: int,
    views: int,
    preserve: int,
    reports: int,
    trust: int,
    urgent: int = 0,
    *,
    account_type: str = "public",
    sanction_level: int = 0,
    sort_tab: str = "weekly_hot",
    evidence_grade: str = "B",
    evidence_hours_left: int | None = None,
) -> float:
    w1, w2, w3, w4, w5, w6 = 1.0, 1.3, 0.2, 3.0, 1.8, 1.1
    base = (up * w1) + (comments * w2) + (views * w3) + (preserve * w4) - (reports * w5) + (trust * w6)
    account = _normalize_account_type(account_type)
    tab = _normalize_tab(sort_tab)
    exposure = _ACCOUNT_EXPOSURE_MULTIPLIER[account]
    sanction_penalty = max(0.5, 1.0 - (max(0, min(int(sanction_level), 5)) * 0.06))
    grade = str(evidence_grade).strip().upper()
    grade_multiplier = {"A": 1.06, "B": 1.0, "C": 0.9}.get(grade, 1.0)
    countdown_multiplier = 1.0
    if evidence_hours_left is not None:
        remaining = max(0, int(evidence_hours_left))
        if remaining <= 12:
            countdown_multiplier = 0.9
        elif remaining <= 24:
            countdown_multiplier = 0.95
    score = base * exposure * sanction_penalty * _TAB_SCORE_MULTIPLIER[tab] * grade_multiplier * countdown_multiplier
    return score + urgent


def apply_report_threshold(status: str, reports: int, threshold: int) -> str:
    if reports >= threshold:
        return "hidden"
    return status


def apply_policy_transition(
    status: str,
    reports: int,
    severity: int,
    appeal: bool,
    *,
    account_type: str = "alias",
    verified: bool = False,
    sanction_level: int = 0,
    appeal_accepted: bool | None = None,
) -> tuple[str, dict]:
    thresholds = _thresholds_for(account_type, verified)
    current_level = max(0, min(5, int(sanction_level)))
    sev = max(0, int(severity))

    if appeal and status in {"hidden", "locked", "ghost"}:
        accepted = appeal_accepted if appeal_accepted is not None else (verified or sev <= 1)
        if accepted:
            rollback = {
                "hidden": "visible",
                "locked": "hidden",
                "ghost": "locked",
            }
            next_status = rollback[status]
            next_level = max(0, current_level - 1)
            return next_status, {
                "action_type": "APPEAL",
                "appeal_result": "accepted",
                "prev_status": status,
                "next_status": next_status,
                "reason_rule_id": "RULE-PLZ-SAN-02",
                "sanction_level": next_level,
            }
        return status, {
            "action_type": "APPEAL_REJECT",
            "appeal_result": "rejected",
            "prev_status": status,
            "next_status": status,
            "reason_rule_id": "RULE-PLZ-SAN-03",
            "sanction_level": current_level,
        }

    if status == "visible" and reports >= thresholds["hidden"]:
        next_status = "hidden"
        return next_status, {
            "action_type": "HIDE_PREVIEW",
            "prev_status": status,
            "next_status": next_status,
            "reason_rule_id": "RULE-PLZ-MOD-01",
            "sanction_level": compute_sanction_level(reports, sev, next_status),
        }
    if status == "hidden" and (reports >= thresholds["locked"] or sev >= 2):
        next_status = "locked"
        return next_status, {
            "action_type": "LOCK_THREAD",
            "prev_status": status,
            "next_status": next_status,
            "reason_rule_id": "RULE-PLZ-MOD-02",
            "sanction_level": compute_sanction_level(reports, sev, next_status),
        }
    if status == "locked" and (reports >= thresholds["ghost"] or sev >= 2):
        next_status = "ghost"
        return next_status, {
            "action_type": "GHOST_THREAD",
            "prev_status": status,
            "next_status": next_status,
            "reason_rule_id": "RULE-PLZ-MOD-03",
            "sanction_level": compute_sanction_level(reports, sev, next_status),
        }
    if status == "ghost" and (reports >= thresholds["sanctioned"] or sev >= 3):
        next_status = "sanctioned"
        return next_status, {
            "action_type": "SANCTION_USER",
            "prev_status": status,
            "next_status": next_status,
            "reason_rule_id": "RULE-PLZ-SAN-01",
            "sanction_level": compute_sanction_level(reports, sev, next_status),
        }

    return status, {
        "action_type": "NO_OP",
        "prev_status": status,
        "next_status": status,
        "reason_rule_id": "RULE-PLZ-UI-01",
        "sanction_level": max(current_level, compute_sanction_level(reports, sev, status)),
    }


def _thread_score_for_tab(thread: dict, tab: str) -> float:
    safe_tab = _normalize_tab(tab)
    score = compute_score(
        up=int(thread.get("up", 0)),
        comments=int(thread.get("comments", 0)),
        views=int(thread.get("views", 0)),
        preserve=int(thread.get("preserve", 0)),
        reports=int(thread.get("reports", 0)),
        trust=int(thread.get("trust", 0)),
        account_type=str(thread.get("account_type", "public")),
        sanction_level=int(thread.get("sanction_level", 0)),
        sort_tab=safe_tab,
    )
    evidence = float(thread.get("evidence", 0.0))
    preserve = float(thread.get("preserve", 0.0))
    trust = float(thread.get("trust", 0.0))
    comments = float(thread.get("comments", 0.0))
    up = float(thread.get("up", 0.0))
    views = float(thread.get("views", 0.0))
    reports = float(thread.get("reports", 0.0))
    age_hours = float(thread.get("age_hours", 0.0))

    if safe_tab == "latest":
        return (-age_hours * 2.0) + (score * 0.01)
    if safe_tab == "evidence_first":
        return (evidence * 3.2) + (trust * 1.5) + (score * 0.2) - (age_hours * 0.02)
    if safe_tab == "preserve_first":
        return (preserve * 3.1) + (trust * 1.1) + (score * 0.2) - (reports * 0.4)
    return score + (up * 0.8) + (comments * 1.2) + (views * 0.07) - (reports * 0.8) - (age_hours * 0.03)


def rank_threads_for_tab(threads: Iterable[dict], tab: str) -> list[dict]:
    scored: list[dict] = []
    for row in threads:
        item = dict(row)
        item["tab_score"] = round(_thread_score_for_tab(item, tab), 6)
        scored.append(item)
    scored.sort(key=lambda item: (-float(item["tab_score"]), str(item.get("thread_id", ""))))
    return scored
