import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

if "message" in st.session_state:
    st.success(st.session_state["message"])
    del st.session_state["message"]

from supabase import create_client

SUPABASE_URL = "https://pwtlcixcykpqfjlhyzxv.supabase.co"
SUPABASE_KEY = "sb_publishable_LMC-zFPQqTFA5dptZA5SXQ_ij7T1TVJ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("➕ Add / Update Lead")

file_path = "crm_data.csv"

callers = ["Ravi", "Aman", "Shivam"]

not_connected_dispositions = [
    "Not Connected 1st-Attempt",
    "Not Connected 2nd-Attempt",
    "Not Connected 3rd-Attempt",
    "Not Connected 4th-Attempt",
    "Invalid/Wrong Number"
]

connected_dispositions = [
    "Meeting Scheduled (BD)",
    "Meet Later (Qualified)",
    "Call Later (Interested)",
    "Call Later (Under Construction)",
    "Not Interested in Solar",
]

# ---------------- LOAD DATA ----------------

if os.path.exists(file_path):
    df_existing = pd.read_csv(file_path)
else:
    df_existing = pd.DataFrame()

# ---------------- PHONE CLEAN ----------------

def clean_phone(phone):
    phone = phone.strip().replace(" ", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    if phone.startswith("0"):
        phone = phone[1:]
    return phone

# ---------------- ROUND ROBIN ----------------

def get_next_caller():
    if not df_existing.empty:
        count = len(df_existing)
    else:
        count = 0
    return callers[count % len(callers)]

# ---------------- PHONE INPUT ----------------

raw_phone = st.text_input("Phone Number (10 digit)")
phone = clean_phone(raw_phone)

existing_lead = None

if phone.isdigit() and len(phone) == 10:

    check = supabase.table("leads") \
        .select("*") \
        .eq("phone", phone) \
        .execute()

    if check.data:
        existing_lead = check.data[0]

        st.warning("⚠ Existing lead found. You can modify this lead and click Save.")

# ---------------- BASIC FIELDS ----------------

name = st.text_input("Customer Name")
city = st.text_input("City")
call_status = st.selectbox("Call Status", ["Not Connected", "Connected"])

if city.lower() in ["kanpur", "lucknow"]:
    assigned_caller = get_next_caller()
    st.success(f"Auto Assigned to {assigned_caller}")
else:
    assigned_caller = st.selectbox("Assign Caller", callers)

# ---------------- DISPOSITION ----------------

if call_status == "Not Connected":
    disposition = st.selectbox("Disposition", not_connected_dispositions)
else:
    disposition = st.selectbox("Disposition", connected_dispositions)

# ---------------- MEETING SECTION ----------------

meeting_date = None
meeting_slot = None
meeting_address = None
callback_date = None
callback_slot = None

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

if call_status == "Connected" and disposition == "Meeting Scheduled (BD)":

    st.subheader("📅 Meeting Details")

    meeting_date_raw = st.date_input("Meeting Date")
    meeting_slot = st.selectbox("Meeting Time Slot", time_slots)
    meeting_address = st.text_area("Meeting Address")

    meeting_date = meeting_date_raw.strftime("%d-%b-%y")

# ---------------- CALLBACK SECTION ----------------

if call_status == "Connected" and "Call Later" in disposition:

    st.subheader("⏳ Callback Details")

    callback_date_raw = st.date_input("Callback Date")
    callback_slot = st.selectbox("Callback Time Slot", time_slots)

    callback_date = callback_date_raw.strftime("%d-%b-%y")

remarks = st.text_area("Remarks")

# ---------------- SAVE ----------------

if st.button("Save Lead"):

    if not phone.isdigit():
        st.error("Mobile must contain only digits.")
        st.stop()

    if len(phone) != 10:
        st.error("Mobile must be exactly 10 digits.")
        st.stop()

    # Fetch existing lead by phone
    existing = supabase.table("leads") \
        .select("*") \
        .eq("phone", phone) \
        .execute()

    old_data = existing.data[0] if existing.data else None

    data = {
        "name": name,
        "phone": phone,
        "city": city,
        "call_status": call_status,
        "disposition": disposition,
        "meeting_date": meeting_date if meeting_date else None,
        "meeting_address": meeting_address if meeting_address else None,
        "callback_date": callback_date if callback_date else None,
        "remarks": remarks
    }

    # UPSERT lead
    response = supabase.table("leads").upsert(
        data,
        on_conflict="phone"
    ).execute()

    # 🔥 HISTORY INSERT
    if old_data:

        lead_id = old_data["id"]

        for field in data.keys():

            old_val = str(old_data.get(field))
            new_val = str(data.get(field))

            if old_val != new_val:

                supabase.table("lead_history").insert({
                    "lead_id": lead_id,
                    "updated_field": field,
                    "old_value": old_val,
                    "new_value": new_val
                }).execute()

    if response.data:
        st.success("Lead saved successfully!")
        st.rerun()
    else:
        st.error("Error saving lead")