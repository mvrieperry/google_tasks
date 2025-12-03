## This is a Python Script for adding tasks to Google calendar

"""
create_60_day_hard_tasks.py

Create a "60 Day Hard" program in Google Tasks, mirroring the Google Apps Script
version that runs from Jan 5, 2026 for 60 days.

Requires:
- credentials.json in the repo root (OAuth client for Google Tasks API)
- python -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""
#pip install google-api-python-client 
#pip install google-auth-httplib2 
#pip install google-auth-oauthlib

from __future__ import annotations

import datetime as dt
import os
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Google Tasks scope (full access to your Tasks)
SCOPES = ["https://www.googleapis.com/auth/tasks"]

# Name of the task list to create/use
TASKLIST_NAME = "60 Day Hard"


def get_service():
    """
    Authenticate and return a Google Tasks API service client.
    Looks for token.json and credentials.json in the current working directory.
    """
    creds: Optional[Credentials] = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json not found. "
                    "Download it from Google Cloud Console and place it next to this script."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("tasks", "v1", credentials=creds)


def get_or_create_tasklist(service, name: str) -> Dict[str, Any]:
    """
    Find an existing task list by title, or create it if it doesn't exist.
    """
    result = service.tasklists().list().execute()
    items = result.get("items", []) or []

    for lst in items:
        if lst.get("title") == name:
            return lst

    body = {"title": name}
    return service.tasklists().insert(body=body).execute()


def make_due_iso(date_obj: dt.date) -> str:
    """
    Convert a date to an RFC3339 "due" string at noon UTC.
    Google Tasks due dates are datetime strings in RFC3339 format.
    """
    dt_noon = dt.datetime(
        year=date_obj.year,
        month=date_obj.month,
        day=date_obj.day,
        hour=12,
        minute=0,
        second=0,
        tzinfo=dt.timezone.utc,
    )
    # Example: 2026-01-05T12:00:00Z
    return dt_noon.isoformat().replace("+00:00", "Z")


def create_task(
    service,
    tasklist_id: str,
    title: str,
    notes: Optional[str] = None,
    due: Optional[str] = None,
):
    """
    Create a single task in the specified task list.
    """
    body: Dict[str, Any] = {"title": title}
    if notes:
        body["notes"] = notes
    if due:
        body["due"] = due

    return service.tasks().insert(tasklist=tasklist_id, body=body).execute()


def main():
    """
    Main entrypoint: create all tasks for the 60 Day Hard program.
    Mirrors the original JS logic:

    - Start date: Monday Jan 5, 2026
    - numDays: 60
    - Week A / Week B alternation based on week index (i // 7)
    - Daily:
        - "60DH – Daily Habits"
        - "60DH – 30-min Walk" OR "60DH – Long Walk" on Sundays
    - Day-specific tasks (Mon–Sun) including climb/swim alternation on Thursdays
    """
    service = get_service()
    tasklist = get_or_create_tasklist(service, TASKLIST_NAME)
    tasklist_id = tasklist["id"]

    # Start date: Monday Jan 5, 2026 (Week A start)
    start_date = dt.date(2026, 1, 5)
    num_days = 60

    for i in range(num_days):
        current_date = start_date + dt.timedelta(days=i)
        # Python: Monday = 0, Sunday = 6
        dow = current_date.weekday()
        week_index = i // 7
        is_week_a = (week_index % 2 == 0)

        due = make_due_iso(current_date)

        # === DAILY HABITS TASK ===
        daily_notes = "\n".join(
            [
                "No alcohol",
                "No recreational drugs",
                "2L water",
                "5 min meditation and RLT",
                "Reading before bed",
            ]
        )
        create_task(
            service,
            tasklist_id,
            title="60DH – Daily Habits",
            notes=daily_notes,
            due=due,
        )

        # === DAILY WALK ===
        # In original JS: Sunday (0) = long walk. Here, Sunday is dow == 6.
        if dow == 6:
            walk_title = "60DH – Long Walk (45–60 min)"
        else:
            walk_title = "60DH – 30-min Walk"

        create_task(service, tasklist_id, title=walk_title, due=due)

        # === DAY-SPECIFIC WORKOUTS ===
        # Map original JS getDay() cases to Python weekday():
        # JS: 1 = Mon → Python: 0
        # JS: 2 = Tue → Python: 1
        # JS: 3 = Wed → Python: 2
        # JS: 4 = Thu → Python: 3
        # JS: 5 = Fri → Python: 4
        # JS: 6 = Sat → Python: 5
        # JS: 0 = Sun → Python: 6

        if dow == 0:  # MONDAY – Strength – Full Body / Lower
            notes = "\n".join(
                [
                    "20–25 min cardio",
                    "Push-ups: 3×12",
                    "Pull-ups (assisted): 3×8 (2–3s hold)",
                    "Step-ups: 3×10/leg",
                    "Leg raises: 3×10",
                    "Stretch",
                ]
            )
            create_task(
                service,
                tasklist_id,
                title="Strength – Full Body / Lower",
                notes=notes,
                due=due,
            )

        elif dow == 1:  # TUESDAY – Climb
            notes = "\n".join(
                [
                    "4–6 routes",
                    "Technique warm-up",
                    "Shoulder mobility",
                ]
            )
            create_task(
                service,
                tasklist_id,
                title="Climbing Session",
                notes=notes,
                due=due,
            )

        elif dow == 2:  # WEDNESDAY – Signature Strength
            notes = "\n".join(
                [
                    "25 min cardio",
                    "Push-ups: 3×12",
                    "Pull-ups: 3×8",
                    "Step-ups: 3×10/leg",
                    "Leg raises: 3×10",
                    "Stretch",
                ]
            )
            create_task(
                service,
                tasklist_id,
                title="Strength – Signature Workout",
                notes=notes,
                due=due,
            )

        elif dow == 3:  # THURSDAY — Week A = Climb, Week B = Swim
            if is_week_a:
                notes = "\n".join(
                    [
                        "4–6 routes",
                        "Technique focus",
                        "Mobility cool-down",
                    ]
                )
                create_task(
                    service,
                    tasklist_id,
                    title="Climbing Session (Week A)",
                    notes=notes,
                    due=due,
                )
            else:
                notes = "\n".join(
                    [
                        "750–1000m total",
                        "4×50 warm-up",
                        "6×50 drills",
                        "4×100 easy",
                        "2×50 cooldown",
                    ]
                )
                create_task(
                    service,
                    tasklist_id,
                    title="Swim Session (Week B)",
                    notes=notes,
                    due=due,
                )

        elif dow == 4:  # FRIDAY – Strength + Core
            notes = "\n".join(
                [
                    "20 min cardio",
                    "Push-ups: 3×10–12",
                    "Pull-ups: 3×6–8",
                    "Split squats or step-ups: 3×8/leg",
                    "Core circuit ×3",
                    "Stretch",
                ]
            )
            create_task(
                service,
                tasklist_id,
                title="Strength – Full Body + Core",
                notes=notes,
                due=due,
            )

        elif dow == 5:  # SATURDAY – Yoga
            create_task(
                service,
                tasklist_id,
                title="Yoga – 1 Hour",
                due=due,
            )

        # SUNDAY – Active Recovery (Mobility / Recovery)
        if dow == 6:
            create_task(
                service,
                tasklist_id,
                title="Mobility / Recovery",
                due=due,
            )


if __name__ == "__main__":
    main()
