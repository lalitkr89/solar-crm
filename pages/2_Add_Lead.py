import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# ---------------- SUPABASE ----------------

SUPABASE_URL = "https://pwtlcixcykpqfjlhyzxv.supabase.co"
SUPABASE_KEY = "sb_publishable_LMC-zFPQqTFA5dptZA5SXQ_ij7T1TVJ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("➕ Add / Update Lead")

# ---------------- CALLERS ----------------

callers = ["Ravi", "Aman", "Shivam"]

# ---------------- DISPOSITIONS ----------------

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

# ---------------- PHONE CLEAN ----------------


def clean_phone(phone):

    if not phone:
        return ""

    phone = phone.strip().replace(" ", "")

    if phone.startswith("+91"):
        phone = phone[3:]

    if phone.startswith("0"):
        phone = phone[1:]

    return phone


# ---------------- ROUND ROBIN ----------------


def get_next_caller():

    try:
        count = supabase.table("leads").select("id").execute()
        total = len(count.data) if count.data else 0
        return callers[total % len(callers)]
    except:
        return callers[0]


# ---------------- PHONE INPUT ----------------

raw_phone = st.text_input("Phone Number (10 digit)")
phone = clean_phone(raw_phone)

existing_lead = None

if phone.isdigit() and len(phone) == 10:

    try:
        check = supabase.table("leads").select("*").eq("phone", phone).execute()

        if check.data:

            existing_lead = check.data[0]

            st.warning("⚠ Existing lead found. Edit details and click Save.")

    except Exception as e:
        st.error(e)


# ---------------- BASIC FIELDS ----------------

name = st.text_input("Customer Name")
city = st.text_input("City")

call_status = st.selectbox("Call Connection Status", ["Not Connected", "Connected"])

# ---------------- CALLER ASSIGN ----------------

if city.lower() in ["kanpur", "lucknow"]:

    assigned_caller = get_next_caller()
    st.success(f"Auto Assigned to {assigned_caller}")

else:

    assigned_caller = st.selectbox("Assign Caller", callers)

# ---------------- DISPOSITION ----------------

if call_status == "Not Connected":

    disposition = st.selectbox("Pre Sales Disposition", not_connected_dispositions)

else:

    disposition = st.selectbox("Pre Sales Disposition", connected_dispositions)

# ---------------- TIME SLOTS ----------------

time_slots = [
    "09:00-10:00",
    "10:00-11:00",
    "11:00-12:00",
    "12:00-13:00",
    "13:00-14:00",
    "14:00-15:00",
    "15:00-16:00",
    "16:00-17:00",
    "17:00-18:00",
    "18:00-19:00",
]

meeting_date = None
meeting_slot = None
meeting_address = None

callback_date = None
callback_slot = None

# ---------------- MEETING ----------------

if call_status == "Connected" and disposition == "Meeting Scheduled (BD)":

    st.subheader("📅 Meeting Details")

    meeting_date_raw = st.date_input("Meeting Date")

    meeting_slot = st.selectbox("Meeting Time Slot", time_slots)

    meeting_address = st.text_area("Meeting Address")

    meeting_date = meeting_date_raw.isoformat()

# ---------------- CALLBACK ----------------

if call_status == "Connected" and "Call Later" in disposition:

    st.subheader("⏳ Callback Details")

    callback_date_raw = st.date_input("Callback Date")

    callback_slot = st.selectbox("Callback Time Slot", time_slots)

    callback_date = callback_date_raw.isoformat()

# ---------------- REMARKS ----------------

remarks = st.text_area("Remarks")

# ---------------- SAVE ----------------

if st.button("Save Lead"):

    if not phone.isdigit():
        st.error("Mobile must contain only digits.")
        st.stop()

    if len(phone) != 10:
        st.error("Mobile must be exactly 10 digits.")
        st.stop()

    try:

        existing = supabase.table("leads").select("*").eq("phone", phone).execute()

        old_data = existing.data[0] if existing.data else None

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
            "assigned_to": None,
            "remarks": remarks,
            "created_at": datetime.now().isoformat(),
        }

        response = supabase.table("leads").upsert(data, on_conflict="phone").execute()

        if response.data:

            lead_id = response.data[0]["id"]

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
