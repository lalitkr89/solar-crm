import streamlit as st
import pandas as pd
import time
from supabase import create_client

phone = st.session_state.get("selected_lead")

if not phone:
    st.warning("No lead selected")
    st.stop()

st.set_page_config(page_title="Lead Details", layout="wide")

# -------- SUPABASE --------

SUPABASE_URL = "https://pwtlcixcykpqfjlhyzxv.supabase.co"
SUPABASE_KEY = "sb_publishable_LMC-zFPQqTFA5dptZA5SXQ_ij7T1TVJ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------- HISTORY FUNCTION --------


def log_history(old_data, new_data, lead_id):

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


# -------- DISPOSITION LIST --------

not_connected_dispositions = [
    "Not Connected 1st-Attempt",
    "Not Connected 2nd-Attempt",
    "Not Connected 3rd-Attempt",
    "Not Connected 4th-Attempt",
    "Invalid/Wrong Number",
]

connected_dispositions = [
    "Meeting Scheduled (BD)",
    "Meet Later (Qualified)",
    "Call Later (Interested)",
    "Call Later (Under Construction)",
    "Language Barrier",
    "Non Qualified - Roof Area Insufficient",
    "Non Qualified - Bill Amount Insufficient",
    "Non Qualified - No Roof Ownership",
    "Non Qualified - Not Govt Meter",
    "Non Qualified - Meter Connection Not Yet Available",
    "Not Serviceable - Offgrid Enquiry",
    "Not Serviceable - SS not in location",
    "Not Interested in Solar",
    "Not Interested in Solar - Price Issue",
    "Housing Society Enquiry",
    "Commercial Lead",
    "SolarPro Enquiry",
]

# -------- TIME SLOTS --------

time_slots = [
    "09:00 - 10:00",
    "10:00 - 11:00",
    "11:00 - 12:00",
    "12:00 - 13:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00",
    "16:00 - 17:00",
    "17:00 - 18:00",
    "18:00 - 19:00",
]

# -------- GET SELECTED LEAD --------

phone = st.session_state.get("selected_lead")

if not phone:
    st.warning("No lead selected.")
    st.stop()

# -------- FETCH LEAD --------

res = supabase.table("leads").select("*").eq("phone", phone).execute()

df = pd.DataFrame(res.data)

if df.empty:
    st.error("Lead not found.")
    st.stop()

lead = df.iloc[0]

# -------- LEAD TIMER --------

if "lead_start_time" not in st.session_state:
    st.session_state.lead_start_time = time.time()

time_spent = int(time.time() - st.session_state.lead_start_time)

st.info(f"⏱ Time spent on this lead: {time_spent} seconds")

# -------- EDIT LEAD DIALOG --------


@st.dialog("Edit Lead")
def edit_lead_dialog(lead):

    new_name = st.text_input("Name", value=lead["name"])
    new_city = st.text_input("City", value=lead["city"])

    new_status = st.selectbox(
        "Call Status",
        ["Connected", "Not Connected"],
        index=0 if lead["call_status"] == "Connected" else 1,
    )

    if new_status == "Connected":
        disposition_list = connected_dispositions
    else:
        disposition_list = not_connected_dispositions

    new_disposition = st.selectbox(
        "Disposition",
        disposition_list,
        index=(
            disposition_list.index(lead["disposition"])
            if lead["disposition"] in disposition_list
            else 0
        ),
    )

    new_remarks = st.text_area("Remarks", value=lead["remarks"])

    meeting_date = None
    meeting_slot = None
    callback_date = None
    callback_slot = None

    if new_disposition == "Meeting Scheduled (BD)":

        meeting_date = st.date_input(
            "Meeting Date",
            value=(lead["meeting_date"] if pd.notnull(lead["meeting_date"]) else None),
        )

        meeting_slot = st.selectbox("Meeting Slot", time_slots)

    if "Call Later" in new_disposition:

        callback_date = st.date_input(
            "Callback Date",
            value=(
                lead["callback_date"] if pd.notnull(lead["callback_date"]) else None
            ),
        )

        callback_slot = st.selectbox("Callback Slot", time_slots)

    if st.button("💾 Save Changes"):

        existing = supabase.table("leads").select("*").eq("id", lead["id"]).execute()
        old_data = existing.data[0]

        new_data = {
            "name": new_name,
            "city": new_city,
            "call_status": new_status,
            "disposition": new_disposition,
            "meeting_date": meeting_date.isoformat() if meeting_date else None,
            "meeting_slot": meeting_slot,
            "callback_date": callback_date.isoformat() if callback_date else None,
            "callback_slot": callback_slot,
            "remarks": new_remarks,
            "lead_status": "processed",
        }

        supabase.table("leads").update(new_data).eq("id", lead["id"]).execute()

        log_history(old_data, new_data, lead["id"])

        st.success("Lead Updated Successfully")

        # -------- RESET TIMER --------
        st.session_state.lead_start_time = time.time()

        # -------- LOAD NEXT LEAD --------
        next_lead = (
            supabase.table("leads")
            .select("*")
            .eq("lead_status", "open")
            .limit(1)
            .execute()
        )

        if next_lead.data:
            st.session_state.selected_lead = next_lead.data[0]["phone"]
            st.rerun()


# -------- TITLE + ACTION BAR --------

header_left, header_right = st.columns([1, 3], vertical_alignment="center")

with header_left:
    st.markdown("### 👤 Lead Details")

with header_right:

    phone_number = lead["phone"]

    b1, b2, b3, b4, b5 = st.columns(5, gap="small")

    with b1:
        st.link_button(
            "📞Call", f"tel:{phone_number}", use_container_width=True, help="Call"
        )

    with b2:
        st.link_button(
            "💬WA",
            f"https://wa.me/91{phone_number}",
            use_container_width=True,
            help="WhatsApp",
        )

    with b3:
        st.link_button(
            "📍Map",
            f"https://www.google.com/maps/search/{lead.get('city','')}",
            use_container_width=True,
            help="Map",
        )

    with b4:
        if st.button("📝Edit Lead", use_container_width=True, help="Edit Lead"):
            edit_lead_dialog(lead)

    if "show_history" not in st.session_state:
        st.session_state.show_history = False

    with b5:
        label = "❌History" if st.session_state.show_history else "📜History"

        if st.button(label, use_container_width=True, help="Toggle History"):
            st.session_state.show_history = not st.session_state.show_history
            st.rerun()

# -------- LEADCARD --------


c1, c2, c3 = st.columns(3)

with c1:
    st.write("👤 Name:", lead["name"])
    st.write("📞 Phone:", lead["phone"])
    st.write("📍 City:", lead["city"])
    st.write("📝 Remarks:", lead["remarks"] if lead["remarks"] else "-")

with c2:
    st.write("📊 Disposition:", lead["disposition"])
    st.write("☎️ Call Status:", lead["call_status"])
    st.write("👨 Assigned Caller:", lead["assigned_to"])

with c3:
    st.write("📅 Callback Date:", lead["callback_date"])
    st.write("📅 Meeting Date:", lead["meeting_date"])
    st.write("🕒 Created:", lead["created_at"])
# -------- TIMELINE --------

if st.session_state.show_history:

    st.markdown("---")
    st.subheader("📜 Activity Timeline")

    history_res = (
        supabase.table("lead_history")
        .select("*")
        .eq("lead_id", lead["id"])
        .order("updated_at", desc=True)
        .execute()
    )

    history_df = pd.DataFrame(history_res.data)

    if history_df.empty:

        st.info("No history available.")

    else:

        history_df["updated_at"] = (
            pd.to_datetime(history_df["updated_at"])
            .dt.tz_localize("UTC")
            .dt.tz_convert("Asia/Kolkata")
        )

        for _, h in history_df.iterrows():

            st.markdown(
                f"""
**{h['updated_at'].strftime('%d %b %Y | %I:%M %p')}**

**{h['updated_field']}**

{h['old_value']} ➜ {h['new_value']}

---
"""
            )
