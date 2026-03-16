from core.database import supabase
from services.caller_service import get_caller_names


def get_next_caller(team="pre-sales"):
    """Round-robin next caller from users table"""
    try:
        callers = get_caller_names(team=team)
        if not callers:
            return None

        res = (
            supabase.table("leads")
            .select("assigned_to")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not res.data:
            return callers[0]

        last = res.data[0]["assigned_to"]
        if last not in callers:
            return callers[0]

        idx = callers.index(last)
        return callers[(idx + 1) % len(callers)]

    except Exception:
        callers = get_caller_names(team=team)
        return callers[0] if callers else None
