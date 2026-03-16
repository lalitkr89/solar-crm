import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.title("📅 Today’s Action Center")

file_path = "crm_data.csv"

if not os.path.exists(file_path):
    st.info("No data available.")
    st.stop()

df = pd.read_csv(file_path)

if df.empty:
    st.info("No leads available.")
    st.stop()

today_str = datetime.now().strftime("%d-%b-%y")

# ---------------- TODAY MEETINGS ----------------

st.subheader("🏠 Today’s Meetings")

today_meetings = df[df["Meeting_Date"] == today_str]

if not today_meetings.empty:
    st.dataframe(today_meetings.sort_values("Meeting_Slot"))
else:
    st.success("No meetings scheduled for today ✅")

# ---------------- TODAY CALLBACKS ----------------

st.subheader("📞 Today’s Callbacks")

today_callbacks = df[df["Callback_Date"] == today_str]

if not today_callbacks.empty:
    st.dataframe(today_callbacks.sort_values("Callback_Slot"))
else:
    st.success("No callbacks scheduled for today ✅")
