from datetime import datetime, timedelta
from typing import List, Dict, Any

from camp_class import read_from_file


def _parse_date(date_str: str) -> datetime:
    """Parse date string YYYY-MM-DD; fallback to today on error."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return datetime.now()


def _date_range(start: datetime, end: datetime):
    """Yield dates from start to end inclusive."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def generate_schedule_events(include_activities: bool = True) -> List[Dict[str, Any]]:
    """
    Build a flat list of schedule events from camp data.

    Each event dict includes:
    - type: "camp" or "activity"
    - camp: camp name
    - detail: text description
    - start: datetime (day-level)
    - end: datetime (day-level)
    - leaders: list of usernames
    - location: camp location
    - metadata: extra info (camp_type, etc.)
    """
    camps = read_from_file()
    events: List[Dict[str, Any]] = []

    def _fmt_activity(act) -> str:
        if isinstance(act, dict):
            title = act.get("activity") or act.get("title") or act.get("name") or "Activity"
            time = act.get("time")
            if time:
                return f"{title} @ {time}"
            return str(title)
        return str(act)

    for camp in camps:
        start_dt = _parse_date(camp.start_date)
        end_dt = _parse_date(camp.end_date)
        leaders = list(camp.scout_leaders)
        camp_type_label = {1: "Day", 2: "Overnight", 3: "Multi-day"}.get(camp.camp_type, "Camp")
        events.append(
            {
                "type": "camp",
                "camp": camp.name,
                "detail": f"{camp_type_label} window {camp.start_date} \u2192 {camp.end_date}",
                "start": start_dt,
                "end": end_dt,
                "leaders": leaders,
                "location": camp.location,
                "metadata": {
                    "camp_type": camp.camp_type,
                    "camp_type_label": camp_type_label,
                    "campers": len(camp.campers),
                },
            }
        )
        if not include_activities:
            continue
        for date_str, acts in (camp.activities or {}).items():
            try:
                act_date = _parse_date(date_str)
            except Exception:
                act_date = start_dt
            for act in acts:
                detail_str = _fmt_activity(act)
                events.append(
                    {
                        "type": "activity",
                        "camp": camp.name,
                        "detail": detail_str,
                        "start": act_date,
                        "end": act_date,
                        "leaders": leaders,
                        "location": camp.location,
                        "metadata": {"raw_activity": act},
                    }
                )

    events.sort(key=lambda e: (e["start"], 0 if e["type"] == "camp" else 1, e["camp"]))
    return events


def find_conflicts(events: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    """
    Identify potential conflicts: same leader booked on multiple camps the same day.
    (Activities within the same camp/day are not flagged.)
    Returns a mapping of event index -> list of conflicting leaders.
    """
    conflicts: Dict[int, List[str]] = {}
    # Build date -> leader -> indices
    by_date = {}
    for idx, e in enumerate(events):
        day = e["start"].date()
        leaders = e.get("leaders") or []
        for leader in leaders:
            by_date.setdefault((day, leader), []).append(idx)

    for (day, leader), indices in by_date.items():
        # Only flag if leader is on multiple different camps that day
        camps = {events[i].get("camp") for i in indices}
        if len(indices) > 1 and len(camps) > 1:
            for idx in indices:
                conflicts.setdefault(idx, []).append(leader)

    return conflicts
