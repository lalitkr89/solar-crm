from core.database import supabase


def get_all_leads():
    res = supabase.table("leads").select("*").execute()
    return res.data if res.data else []


def get_lead_by_phone(phone):
    res = supabase.table("leads").select("*").eq("phone", phone).execute()
    return res.data[0] if res.data else None


def save_lead(data):
    res = supabase.table("leads").upsert(data, on_conflict="phone").execute()
    return res.data


def update_lead(lead_id, data):
    res = supabase.table("leads").update(data).eq("id", lead_id).execute()
    return res.data
