from datetime import date

# Expected daily submitters
SUBMITTERS = [
    {"name": "Mike Torres", "role": "Concrete Super", "phone": "603-555-0191"},
    {"name": "Ray Delgado", "role": "Framing Super", "phone": "603-555-0147"},
    {"name": "Janet Wu", "role": "Site Foreman", "phone": "603-555-0163"},
]

# One week of raw field submissions
# Covers happy paths + edge cases
SUBMISSIONS = [
    # --- MONDAY ---
    {
        "id": "sub_001",
        "submitter": "Mike Torres",
        "role": "Concrete Super",
        "date": "2026-05-19",
        "raw_input": "Poured the east foundation wall today, went smooth. Had 8 laborers and 2 finishers on site. Rebar crew didn't show until 10am which pushed us back about 90 minutes. No safety issues. Concrete delivery came at 6am as planned. Tomorrow we're stripping forms on the west wall.",
    },
    {
        "id": "sub_002",
        "submitter": "Ray Delgado",
        "role": "Framing Super",
        "date": "2026-05-19",
        "raw_input": "Framing crew finished the north wall section, about 200 linear feet. 6 carpenters on site all day. No delays, lumber delivery came in full. We're actually a half day ahead of where I expected. Safety was fine, no incidents. Tomorrow starting on the south wall.",
    },
    # Janet Wu did NOT submit Monday - triggers reminder
    # --- TUESDAY ---
    {
        "id": "sub_003",
        "submitter": "Mike Torres",
        "role": "Concrete Super",
        "date": "2026-05-20",
        "raw_input": "Stripped forms on the west wall this morning. Found some honeycombing on the lower section, about 3 square feet. Patched it by noon. 6 laborers today. No deliveries scheduled. Behind about 2 hours total from yesterday's late rebar. Tomorrow pouring the west wall if weather holds.",
    },
    {
        "id": "sub_004",
        "submitter": "Ray Delgado",
        "role": "Framing Super",
        "date": "2026-05-20",
        "raw_input": "South wall framing started. Only got 4 carpenters today, two called out sick. Still made decent progress but we lost about 3 hours of productivity. No safety issues. Need another lumber delivery by Thursday or we'll run short. Tomorrow expecting full crew back.",
    },
    {
        "id": "sub_005",
        "submitter": "Janet Wu",
        "role": "Site Foreman",
        "date": "2026-05-20",
        "raw_input": "Overall site was busy today. Coordinated between concrete and framing crews. Had an inspector on site at 2pm for the foundation wall review, passed with no issues. Parking area getting congested with deliveries, need to sort out a staging plan. No safety incidents.",
    },
    # --- WEDNESDAY ---
    {
        "id": "sub_006",
        "submitter": "Mike Torres",
        "role": "Concrete Super",
        "date": "2026-05-21",
        "raw_input": "Weather shut us down at noon, heavy rain came in fast. Only got half a day in. 4 laborers sent home early. West wall pour pushed to Thursday. Nothing else to report.",
    },
    {
        "id": "sub_007",
        "submitter": "Ray Delgado",
        "role": "Framing Super",
        "date": "2026-05-21",
        "raw_input": "Rain hit us hard around 11:30. Full crew of 6 but sent them home by noon. Covered all lumber with tarps. South wall is about 60% framed. Should finish Thursday if weather clears. No safety issues.",
    },
    {
        "id": "sub_008",
        "submitter": "Janet Wu",
        "role": "Site Foreman",
        "date": "2026-05-21",
        "raw_input": "Near miss this morning before the rain - a carpenter almost walked under a suspended load without a hard hat. Stopped it in time, no injury. Did a quick all-hands reminder on PPE. Weather ended the day early. Site secured before we left.",
    },
    # --- THURSDAY ---
    {
        "id": "sub_009",
        "submitter": "Mike Torres",
        "role": "Concrete Super",
        "date": "2026-05-22",
        # Missing crew count - tests edge case handling
        "raw_input": "Poured the west wall today, came out clean. Delivery showed up on time. No delays. Tomorrow starting on the interior footings.",
    },
    {
        "id": "sub_010",
        "submitter": "Ray Delgado",
        "role": "Framing Super",
        "date": "2026-05-22",
        "raw_input": "Finished south wall framing, full crew of 6 back today. Started on the east wall headers. Lumber delivery came but was short 40 boards, called supplier and they're bringing the rest Friday morning. About a day ahead of schedule overall. No safety issues.",
    },
    {
        "id": "sub_011",
        "submitter": "Janet Wu",
        "role": "Site Foreman",
        "date": "2026-05-22",
        "raw_input": "Good day overall. Concrete and framing running in parallel without conflicts. Followed up on PPE compliance after yesterday's near miss, everyone wearing gear properly. Delivery staging working better with the new zones I marked. No incidents.",
    },
    # --- FRIDAY ---
    {
        "id": "sub_012",
        "submitter": "Mike Torres",
        "role": "Concrete Super",
        "date": "2026-05-23",
        "raw_input": "Started interior footings, got about 40% done. 7 laborers on site. No issues, good pace. Should finish footings by end of Monday. Concrete truck was 45 minutes late which cost us some time but we made most of it up.",
    },
    {
        "id": "sub_013",
        "submitter": "Ray Delgado",
        "role": "Framing Super",
        "date": "2026-05-23",
        "raw_input": "East wall headers done, moved to roof deck framing. Short lumber delivery arrived this morning as promised. 6 carpenters, solid day. We are now running about a full day ahead of the original schedule. No safety issues. Good week.",
    },
    # Janet Wu did NOT submit Friday - triggers reminder
]

# Track who submitted on each date
def get_submissions_by_date(date_str):
    """Return all submissions for a given date."""
    return [s for s in SUBMISSIONS if s["date"] == date_str]

def get_submission_by_id(sub_id):
    """Return a single submission by ID."""
    return next((s for s in SUBMISSIONS if s["id"] == sub_id), None)

def get_missing_submitters(date_str):
    """Return list of submitters who have not submitted for a given date."""
    submitted_names = [s["submitter"] for s in get_submissions_by_date(date_str)]
    return [p for p in SUBMITTERS if p["name"] not in submitted_names]

def get_all_submissions_for_week(start_date, end_date):
    """Return all submissions between two dates inclusive."""
    return [s for s in SUBMISSIONS if start_date <= s["date"] <= end_date]