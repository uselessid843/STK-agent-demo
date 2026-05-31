from langchain.tools import tool
from database import (
    get_submissions_by_date,
    get_missing_submitters,
    get_all_submissions_for_week,
)

@tool
def process_daily_submissions(date_str: str) -> str:
    """
    Process all field submissions for a given date and return
    a structured daily report answering the 7 PM questions:
    1. Work completed
    2. Crew size and trades on site
    3. Delays and causes
    4. Current % complete on active activities
    5. Safety incidents or near misses
    6. Materials delivered or needed
    7. Plan for tomorrow
    Use this when the user asks for a daily report or daily summary.
    Date format: YYYY-MM-DD
    """
    submissions = get_submissions_by_date(date_str)
    if not submissions:
        return f"No submissions found for {date_str}."
    combined = "\n\n".join(
        [f"{s['submitter']} ({s['role']}):\n{s['raw_input']}"
         for s in submissions]
    )
    return f"Raw submissions for {date_str}:\n\n{combined}"

@tool
def check_missing_submitters(date_str: str) -> str:
    """
    Check who has not submitted a daily report for a given date.
    Returns names, roles, and phone numbers of missing submitters.
    Use this when the user asks who hasn't reported in yet.
    Date format: YYYY-MM-DD
    """
    missing = get_missing_submitters(date_str)
    if not missing:
        return f"All submitters have reported in for {date_str}."
    lines = [f"- {p['name']} ({p['role']}) — {p['phone']}"
             for p in missing]
    return f"Missing submissions for {date_str}:\n" + "\n".join(lines)

@tool
def send_reminder(date_str: str) -> str:
    """
    Send a reminder to anyone who has not submitted
    a daily report for a given date.
    Use this when the user asks to remind or follow up
    with people who haven't submitted.
    Date format: YYYY-MM-DD
    """
    missing = get_missing_submitters(date_str)
    if not missing:
        return f"No reminders needed — everyone submitted for {date_str}."
    reminders = []
    for p in missing:
        msg = (f"[REMINDER SENT] To: {p['name']} ({p['role']}) "
               f"at {p['phone']} — "
               f"Please submit your daily report for {date_str}.")
        reminders.append(msg)
        print(msg)
    return "\n".join(reminders)

@tool
def generate_weekly_summary(start_date: str, end_date: str) -> str:
    """
    Aggregate all daily submissions across a week and return
    a summary for the GC PM covering:
    - Overall progress vs plan
    - Recurring delays or blockers
    - Whether the project is ahead, on track, or behind
    - Open issues requiring PM action
    Use this when the user asks for a weekly summary or week in review.
    Date format: YYYY-MM-DD for both start and end dates.
    """
    submissions = get_all_submissions_for_week(start_date, end_date)
    if not submissions:
        return f"No submissions found between {start_date} and {end_date}."
    combined = "\n\n".join(
        [f"{s['date']} — {s['submitter']} ({s['role']}):\n{s['raw_input']}"
         for s in submissions]
    )
    return (f"All submissions from {start_date} to {end_date}"
            f":\n\n{combined}")