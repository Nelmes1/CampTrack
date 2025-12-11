import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from camp_class import read_from_file
from features.scout import find_camp_by_name
from messaging import load_messages


class CampReport:
    """Generate export packs (CSV + transcript) for a single camp."""

    def __init__(self, camp_name: str):
        self.camp_name = camp_name
        self.camp = find_camp_by_name(camp_name)
        if self.camp is None:
            raise ValueError(f"Camp '{camp_name}' not found.")

    def _camp_duration(self) -> int:
        try:
            start = datetime.strptime(self.camp.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.camp.end_date, "%Y-%m-%d")
            return max((end - start).days + 1, 1)
        except Exception:
            return 0

    def summary_rows(self) -> List[List[Any]]:
        """Rows for CSV export."""
        return [
            ["Camp", self.camp.name],
            ["Location", self.camp.location],
            ["Type", self.camp.camp_type],
            ["Start Date", self.camp.start_date],
            ["End Date", self.camp.end_date],
            ["Duration (days)", self._camp_duration()],
            ["Leaders", ", ".join(self.camp.scout_leaders) or "none"],
            ["Campers", len(self.camp.campers)],
            ["Food Stock", getattr(self.camp, "food_stock", 0)],
            ["Pay Rate", getattr(self.camp, "pay_rate", 0)],
            ["Activities", sum(len(v) for v in (self.camp.activities or {}).values())],
            ["Incidents", len(getattr(self.camp, "incidents", []))],
        ]

    def incident_rows(self) -> List[List[str]]:
        rows = [["Date", "Severity", "Status", "Description", "Campers", "Follow-up", "Reminder", "Resolved At"]]
        for inc in getattr(self.camp, "incidents", []):
            rows.append(
                [
                    inc.get("date", ""),
                    inc.get("severity", ""),
                    inc.get("status", ""),
                    inc.get("description", ""),
                    ", ".join(inc.get("campers", [])),
                    inc.get("follow_up", ""),
                    inc.get("reminder_date", ""),
                    inc.get("resolved_at", ""),
                ]
            )
        return rows

    def activity_rows(self) -> List[List[str]]:
        rows = [["Date", "Activity"]]
        for date_str, acts in (self.camp.activities or {}).items():
            for act in acts:
                label = act.get("activity") if isinstance(act, dict) else str(act)
                rows.append([date_str, label or ""])
        return rows

    def camp_messages(self) -> List[Dict[str, Any]]:
        """Messages tagged with this camp in metadata."""
        msgs = load_messages()
        return [m for m in msgs if (m.get("metadata") or {}).get("camp") == self.camp.name]

    def export(self, target_dir: str) -> Dict[str, str]:
        os.makedirs(target_dir, exist_ok=True)
        base = self.camp.name.replace(" ", "_")
        summary_path = os.path.join(target_dir, f"{base}_summary.csv")
        incidents_path = os.path.join(target_dir, f"{base}_incidents.csv")
        activities_path = os.path.join(target_dir, f"{base}_activities.csv")
        transcript_path = os.path.join(target_dir, f"{base}_messages.txt")

        with open(summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.summary_rows())

        with open(incidents_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.incident_rows())

        with open(activities_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.activity_rows())

        with open(transcript_path, "w") as f:
            msgs = self.camp_messages()
            for msg in msgs:
                flags = []
                if msg.get("priority"):
                    flags.append("PRIORITY")
                if msg.get("requires_ack") and not msg.get("acked"):
                    flags.append("ACK PENDING")
                if msg.get("pinned"):
                    flags.append("PINNED")
                flag_str = f" [{' | '.join(flags)}]" if flags else ""
                attach = msg.get("attachment")
                attach_str = f" [attachment: {attach}]" if attach else ""
                f.write(f"{msg.get('timestamp')} - {msg.get('from')} -> {msg.get('to')}: {msg.get('text')}{flag_str}{attach_str}\n")

        return {
            "summary": summary_path,
            "incidents": incidents_path,
            "activities": activities_path,
            "transcript": transcript_path,
        }


def export_camp_pack(camp_name: str, target_dir: str) -> Dict[str, str]:
    """Facade to export a camp pack."""
    report = CampReport(camp_name)
    return report.export(target_dir)
