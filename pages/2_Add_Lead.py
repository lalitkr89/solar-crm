import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv

st.title("➕ Add / Update Lead")

file_path = "crm_data.csv"

callers = ["Ravi", "Aman", "Shivam"]

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

if not df_existing.empty and phone.isdigit() and len(phone) == 10:
    if phone in df_existing["Phone"].astype(str).values:
        existing_lead = df_existing[df_existing["Phone"].astype(str) == phone].iloc[0]
        st.warning("⚠️ Existing lead detected. Update mode enabled.")

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
        st.error("❌ Mobile must contain only digits.")
        st.stop()

    if len(phone) != 10:
        st.error("❌ Mobile must be exactly 10 digits.")
        st.stop()

    new_data = {
        "Date_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name,
        "Phone": phone,
        "City": city,
        "Assigned_Caller": assigned_caller,
        "Call_Status": call_status,
        "Disposition": disposition,
        "Meeting_Date": meeting_date,
        "Meeting_Slot": meeting_slot,
        "Meeting_Address": meeting_address,
        "Callback_Date": callback_date,
        "Callback_Slot": callback_slot,
        "Remarks": remarks,
    }

    if existing_lead is not None:

        row_index = df_existing.index[df_existing["Phone"].astype(str) == phone][0]

        for col in new_data:
            df_existing.at[row_index, col] = new_data[col]

        df_existing.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)
        st.success("✅ Existing Lead Updated Successfully")

    else:

        new_df = pd.DataFrame([new_data])

        if os.path.exists(file_path):
            new_df.to_csv(
                file_path, mode="a", header=False, index=False, quoting=csv.QUOTE_ALL
            )
        else:
            new_df.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)

        st.success("✅ New Lead Saved Successfully")

    st.rerun()
