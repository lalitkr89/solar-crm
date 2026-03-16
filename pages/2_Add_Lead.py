import streamlit as st
from datetime import datetime
from core.database import supabase
from config.dispositions import not_connected_dispositions, connected_dispositions
from config.time_slots import TIME_SLOTS
from config.callers import CALLERS
from utils.phone_utils import clean_phone
from services.assignment_service import get_next_caller
from services.lead_service import save_lead, get_lead_by_phone

st.title("➕ Add / Update Lead")

# ---------------- PHONE INPUT ----------------

raw_phone = st.text_input("Phone Number (10 digit)")
phone = clean_phone(raw_phone)

existing_lead = None

name_default = ""
city_default = ""
call_status_default = "Not Connected"
disposition_default = not_connected_dispositions[0]
remarks_default = ""

# -------- DUPLICATE CHECK --------

if phone.isdigit() and len(phone) == 10:

    existing_lead = get_lead_by_phone(phone)

    if existing_lead:

        st.warning("⚠ Existing lead found. Edit details and click Save.")

        name_default = existing_lead.get("name", "")
        city_default = existing_lead.get("city", "")
        call_status_default = existing_lead.get("call_status", "Not Connected")
        disposition_default = existing_lead.get(
            "disposition", not_connected_dispositions[0]
        )
        remarks_default = existing_lead.get("remarks", "")

# ---------------- BASIC FIELDS ----------------

name = st.text_input("Customer Name", value=name_default)
city = st.text_input("City", value=city_default)

call_status_index = 0 if call_status_default == "Not Connected" else 1

call_status = st.selectbox(
    "Call Connection Status",
    ["Not Connected", "Connected"],
    index=call_status_index,
)

# ---------------- CALLER ASSIGN ----------------

if city.lower() in ["kanpur", "lucknow"]:

    assigned_caller = get_next_caller()
    st.success(f"Auto Assigned to {assigned_caller}")

else:

    assigned_caller = st.selectbox("Assign Caller", CALLERS)

# ---------------- DISPOSITION ----------------

if call_status == "Not Connected":

    disposition_index = (
        not_connected_dispositions.index(disposition_default)
        if disposition_default in not_connected_dispositions
        else 0
    )

    disposition = st.selectbox(
        "Pre Sales Disposition",
        not_connected_dispositions,
        index=disposition_index,
    )

else:

    disposition_index = (
        connected_dispositions.index(disposition_default)
        if disposition_default in connected_dispositions
        else 0
    )

    disposition = st.selectbox(
        "Pre Sales Disposition",
        connected_dispositions,
        index=disposition_index,
    )

# ---------------- MEETING / CALLBACK ----------------

meeting_date = None
meeting_slot = None
meeting_address = None

callback_date = None
callback_slot = None

# -------- MEETING --------

if call_status == "Connected" and disposition == "Meeting Scheduled (BD)":

    st.subheader("📅 Meeting Details")

    meeting_date_raw = st.date_input("Meeting Date")
    meeting_slot = st.selectbox("Meeting Time Slot", TIME_SLOTS)
    meeting_address = st.text_area("Meeting Address")

    meeting_date = meeting_date_raw.isoformat()

# -------- CALLBACK --------

if call_status == "Connected" and "Call Later" in disposition:

    st.subheader("⏳ Callback Details")

    callback_date_raw = st.date_input("Callback Date")
    callback_slot = st.selectbox("Callback Time Slot", TIME_SLOTS)

    callback_date = callback_date_raw.isoformat()

# ---------------- REMARKS ----------------

remarks = st.text_area("Remarks", value=remarks_default)

# ---------------- SAVE ----------------

if st.button("Save Lead"):

    if not phone.isdigit():
        st.error("Mobile must contain only digits.")
        st.stop()

    if len(phone) != 10:
        st.error("Mobile must be exactly 10 digits.")
        st.stop()

    try:

        existing_lead = get_lead_by_phone(phone)
        old_data = existing_lead

        data = {
            "name": name,
            "phone": phone,
            "city": city,
            "call_status": call_status,
            "disposition": disposition,
            "meeting_date": meeting_date if meeting_date else None,
            "meeting_slot": meeting_slot if meeting_slot else None,
            "meeting_address": meeting_address if meeting_address else None,
            "callback_date": callback_date if callback_date else None,
            "callback_slot": callback_slot if callback_slot else None,
            "assigned_to": assigned_caller,
            "remarks": remarks,
            "created_at": datetime.now().isoformat(),
            "lead_status": "open",
        }

        response = save_lead(data)

        if response:

            lead_id = response[0]["id"]

            if old_data:

                for field in data.keys():

                    old_val = str(old_data.get(field))
                    new_val = str(data.get(field))

                    if old_val != new_val:

                        supabase.table("lead_history").insert(
                            {
                                "lead_id": lead_id,
                                "updated_field": field,
                                "old_value": old_val,
                                "new_value": new_val,
                            }
                        ).execute()

            st.success("✅ Lead Saved Successfully")
            st.rerun()

    except Exception as e:

        st.error("Error saving lead")
        st.write(e)
