import streamlit as st
from supabase import create_client

SUPABASE_URL = "https://pwtlcixcykpqfjlhyzxv.supabase.co"
SUPABASE_KEY = "sb_publishable_LMC-zFPQqTFA5dptZA5SXQ_ij7T1TVJ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="CRM Login", layout="centered")

st.title("🔐 CRM Login")

email = st.text_input("Enter Email")

if st.button("Login"):

    user = supabase.table("users").select("*").eq("email", email).execute()

    if user.data:

        st.session_state.user = user.data[0]

        st.success("Login Successful")

        st.switch_page("pages/1_Dashboard.py")

    else:

        st.error("User not found")
