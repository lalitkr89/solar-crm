import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# ---------------- SESSION ----------------
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "filter_key" not in st.session_state:
    st.session_state.filter_key = 0

if "selected_lead" not in st.session_state:
    st.session_state.selected_lead = None

# ---------------- SUPABASE ----------------
SUPABASE_URL = "https://pwtlcixcykpqfjlhyzxv.supabase.co"
SUPABASE_KEY = "sb_publishable_LMC-zFPQqTFA5dptZA5SXQ_ij7T1TVJ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Pre-Sales CRM", layout="wide")

st.title("📊 Pre-Sales CRM")
st.caption("Lead Tracking Dashboard")


# ---------------- HISTORY FUNCTION ----------------
def log_history(old_data, new_data, lead_id):

    if not old_data:
        return

    for field in new_data.keys():

        old_val = str(old_data.get(field))
        new_val = str(new_data.get(field))

        if old_val != new_val:

            supabase.table("lead_history").insert(
                {
                    "lead_id": lead_id,
                    "updated_field": field,
                    "old_value": old_val,
                    "new_value": new_val,
                }
            ).execute()


# ---------------- FETCH DATA ----------------
users_res = supabase.table("users").select("*").execute()
users_df = pd.DataFrame(users_res.data)

res = supabase.table("leads").select("*").execute()
df = pd.DataFrame(res.data)

if df.empty:
    st.info("No leads available.")
    st.stop()

# ---------------- DATE FORMAT ----------------
df["meeting_date"] = pd.to_datetime(df["meeting_date"], errors="coerce")
df["callback_date"] = pd.to_datetime(df["callback_date"], errors="coerce")
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

# ---------------- MERGE USER NAME ----------------
if not users_df.empty and "assigned_to" in df.columns:

    df = df.merge(
        users_df[["id", "name"]], left_on="assigned_to", right_on="id", how="left"
    )

    df.rename(columns={"name": "assigned_caller"}, inplace=True)

if "assigned_caller" not in df.columns:
    df["assigned_caller"] = "Unassigned"

# ---------------- GLOBAL SEARCH ----------------
search_query = st.text_input("🔎 Global Lead Search (Phone / Name / City / Remarks)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    caller_filter = st.multiselect(
        "Caller",
        sorted(df["assigned_caller"].dropna().unique()),
        key=f"caller_{st.session_state.filter_key}",
    )

with col2:
    city_filter = st.multiselect(
        "City",
        sorted(df["city"].dropna().unique()),
        key=f"city_{st.session_state.filter_key}",
    )

with col3:
    status_filter = st.multiselect(
        "Call Status",
        sorted(df["call_status"].dropna().unique()),
        key=f"status_{st.session_state.filter_key}",
    )

with col4:
    disposition_filter = st.multiselect(
        "Disposition",
        sorted(df["disposition"].dropna().unique()),
        key=f"disp_{st.session_state.filter_key}",
    )

# ---------------- FILTER LOGIC ----------------
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df["phone"]
        .astype(str)
        .str.contains(search_query, case=False, na=False)
        | filtered_df["name"]
        .astype(str)
        .str.contains(search_query, case=False, na=False)
        | filtered_df["city"]
        .astype(str)
        .str.contains(search_query, case=False, na=False)
        | filtered_df["remarks"]
        .astype(str)
        .str.contains(search_query, case=False, na=False)
    ]

if caller_filter:
    filtered_df = filtered_df[filtered_df["assigned_caller"].isin(caller_filter)]

if city_filter:
    filtered_df = filtered_df[filtered_df["city"].isin(city_filter)]

if status_filter:
    filtered_df = filtered_df[filtered_df["call_status"].isin(status_filter)]

if disposition_filter:
    filtered_df = filtered_df[filtered_df["disposition"].isin(disposition_filter)]

# ---------------- KPI ----------------
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Total Leads", len(df))

with k2:
    st.metric("Filtered Leads", len(filtered_df))

with k3:
    st.metric("Connected", len(filtered_df[filtered_df["call_status"] == "Connected"]))

with k4:
    st.metric(
        "Meetings",
        len(filtered_df[filtered_df["disposition"] == "Meeting Scheduled (BD)"]),
    )

# ---------------- LEAD LIST ----------------
filtered_df = filtered_df.sort_values(by="created_at", ascending=False)

st.markdown("### 📋 Leads")

for _, row in filtered_df.iterrows():

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])

    with c1:
        st.write(row["name"])

    with c2:
        st.write(row["phone"])

    with c3:
        st.write(row["city"])

    with c4:
        st.write(row["disposition"])

    with c5:
        if st.button("Open", key=f"open_{row['id']}"):
            st.session_state.selected_lead = row["phone"]
            st.switch_page("pages/4_Lead_Profile.py")
