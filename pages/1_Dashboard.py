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

# ---------------- DATE FILTER ----------------
meeting_start = meeting_end = None
callback_start = callback_end = None

col6, col7, col8, col9, col10 = st.columns(5)

if "Meeting Scheduled (BD)" in disposition_filter:

    with col6:
        meeting_start = st.date_input(
            "Meeting Start Date", key=f"meet_start_{st.session_state.filter_key}"
        )

    with col7:
        meeting_end = st.date_input(
            "Meeting End Date", key=f"meet_end_{st.session_state.filter_key}"
        )

if any("Call Later" in d for d in disposition_filter):

    with col8:
        callback_start = st.date_input(
            "Callback Start Date", key=f"call_start_{st.session_state.filter_key}"
        )

    with col9:
        callback_end = st.date_input(
            "Callback End Date", key=f"call_end_{st.session_state.filter_key}"
        )

with col10:
    if st.button("Reset Filters"):
        st.session_state.filter_key += 1
        st.rerun()

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

if meeting_start:
    filtered_df = filtered_df[
        filtered_df["meeting_date"] >= pd.to_datetime(meeting_start)
    ]

if meeting_end:
    filtered_df = filtered_df[
        filtered_df["meeting_date"] <= pd.to_datetime(meeting_end)
    ]

if callback_start:
    filtered_df = filtered_df[
        filtered_df["callback_date"] >= pd.to_datetime(callback_start)
    ]

if callback_end:
    filtered_df = filtered_df[
        filtered_df["callback_date"] <= pd.to_datetime(callback_end)
    ]

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
            st.rerun()

# ---------------- LEAD PROFILE ----------------
if st.session_state.selected_lead:

    lead_data = filtered_df[filtered_df["phone"] == st.session_state.selected_lead]

    if lead_data.empty:
        st.warning("Selected lead not found in current filters.")

    else:

        lead_row = lead_data.iloc[0]

        st.markdown("---")
        st.markdown("## 👤 Lead Profile")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Name:**", lead_row["name"])
            st.write("**Phone:**", lead_row["phone"])
            st.write("**City:**", lead_row["city"])
            st.write("**Caller:**", lead_row["assigned_caller"])

        with col2:
            st.write("**Call Status:**", lead_row["call_status"])
            st.write("**Disposition:**", lead_row["disposition"])
            st.write("**Meeting Date:**", lead_row["meeting_date"])
            st.write("**Callback Date:**", lead_row["callback_date"])

        st.write("**Remarks:**", lead_row["remarks"])

        colA, colB = st.columns(2)

        with colA:
            if st.button("✏ Edit Lead", key=f"edit_{lead_row['id']}"):
                st.session_state.edit_mode = True

        with colB:
            history_clicked = st.button(
                "🕒 View History", key=f"history_{lead_row['id']}"
            )

            # ---------------- EDIT ----------------
        if st.session_state.edit_mode:

            st.markdown("### ✏ Edit Lead")

            new_name = st.text_input("Name", value=lead_row["name"])

            new_city = st.text_input("City", value=lead_row["city"])

            new_status = st.selectbox(
                "Call Status",
                ["Connected", "Not Connected"],
                index=0 if lead_row["call_status"] == "Connected" else 1,
            )

            dispositions = [
                "Meeting Scheduled (BD)",
                "Meet Later (Qualified)",
                "Call Later (Interested)",
                "Call Later (Under Construction)",
                "Not Interested in Solar",
                "Invalid/Wrong Number",
            ]

            new_disposition = st.selectbox(
                "Disposition",
                dispositions,
                index=(
                    dispositions.index(lead_row["disposition"])
                    if lead_row["disposition"] in dispositions
                    else 0
                ),
            )

            new_meeting_date = st.date_input(
                "Meeting Date",
                value=(
                    lead_row["meeting_date"]
                    if pd.notnull(lead_row["meeting_date"])
                    else None
                ),
            )

            new_callback_date = st.date_input(
                "Callback Date",
                value=(
                    lead_row["callback_date"]
                    if pd.notnull(lead_row["callback_date"])
                    else None
                ),
            )

            new_remarks = st.text_area("Remarks", value=lead_row["remarks"])

            if st.button("Save Changes", key=f"save_{lead_row['id']}"):

                supabase.table("leads").update(
                    {
                        "name": new_name,
                        "city": new_city,
                        "call_status": new_status,
                        "disposition": new_disposition,
                        "meeting_date": (
                            new_meeting_date.isoformat() if new_meeting_date else None
                        ),
                        "callback_date": (
                            new_callback_date.isoformat() if new_callback_date else None
                        ),
                        "remarks": new_remarks,
                    }
                ).eq("id", lead_row["id"]).execute()

                st.success("Lead Updated")

                st.session_state.edit_mode = False
                st.rerun()

        # ---------------- HISTORY ----------------
        if history_clicked:

            history_res = (
                supabase.table("lead_history")
                .select("*")
                .eq("lead_id", lead_row["id"])
                .order("updated_at", desc=True)
                .execute()
            )

            history_df = pd.DataFrame(history_res.data)

            if history_df.empty:
                st.info("No history available.")

            else:

                history_df["updated_at"] = pd.to_datetime(history_df["updated_at"])

                st.markdown("### 🕒 Lead Timeline")

                for _, h in history_df.iterrows():

                    st.markdown(
                        f"""
                    **{h['updated_at'].strftime('%d %b %Y | %I:%M %p')}**

                    **{h['updated_field']}**

                    {h['old_value']} ➜ {h['new_value']}

                    ---
                    """
                    )

        # ---------------- HISTORY ----------------
        if history_clicked:

            history_res = (
                supabase.table("lead_history")
                .select("*")
                .eq("lead_id", lead_row["id"])
                .order("updated_at", desc=True)
                .execute()
            )

            history_df = pd.DataFrame(history_res.data)

            if history_df.empty:
                st.info("No history available.")

            else:

                history_df["updated_at"] = pd.to_datetime(history_df["updated_at"])

                st.markdown("### 🕒 Lead Timeline")

                for _, h in history_df.iterrows():

                    st.markdown(
                        f"""
                    **{h['updated_at'].strftime('%d %b %Y | %I:%M %p')}**

                    **{h['updated_field']}**

                    {h['old_value']} ➜ {h['new_value']}

                    ---
                    """
                    )
