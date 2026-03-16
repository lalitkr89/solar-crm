from core.database import supabase
import streamlit as st


@st.cache_data(ttl=60, show_spinner=False)
def get_active_callers(team="pre-sales"):
    """Get active callers for a team from users table"""
    try:
        res = supabase.table("users")\
            .select("id, name, role, team")\
            .eq("team", team)\
            .eq("is_active", True)\
            .execute()
        return res.data if res.data else []
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def get_caller_names(team="pre-sales"):
    """Get just names list for selectbox"""
    callers = get_active_callers(team)
    return [c["name"] for c in callers]


def get_next_caller_dynamic(team="pre-sales"):
    """Round-robin next caller"""
    try:
        callers = get_caller_names(team)
        if not callers:
            return None

        res = supabase.table("leads")\
            .select("assigned_to")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if not res.data:
            return callers[0]

        last = res.data[0]["assigned_to"]
        if last not in callers:
            return callers[0]

        idx = callers.index(last)
        return callers[(idx + 1) % len(callers)]

    except Exception:
        return None


def clear_callers_cache():
    get_active_callers.clear()
    get_caller_names.clear()
