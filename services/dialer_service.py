from core.database import supabase
from datetime import datetime, timedelta


def get_next_lead(current_lead_id=None):

    now = datetime.now()
    today = now.date().isoformat()
    six_hours_ago = (now - timedelta(hours=6)).isoformat()

    # -------- CALLBACK FIRST --------

    callback = (
        supabase.table("leads")
        .select("*")
        .eq("callback_date", today)
        .limit(1)
        .execute()
    )

    if callback.data:
        return callback.data[0]

    # -------- NEW LEADS --------

    new_lead = (
        supabase.table("leads")
        .select("*")
        .is_("disposition", "null")
        .limit(1)
        .execute()
    )

    if new_lead.data:
        return new_lead.data[0]

    # -------- RETRY NOT CONNECTED --------

    retry = (
        supabase.table("leads")
        .select("*")
        .in_(
            "disposition",
            [
                "Not Connected 1st-Attempt",
                "Not Connected 2nd-Attempt",
                "Not Connected 3rd-Attempt",
                "Not Connected 4th-Attempt",
            ],
        )
        .lte("updated_at", six_hours_ago)
        .limit(1)
        .execute()
    )

    if retry.data:
        return retry.data[0]

    return None
