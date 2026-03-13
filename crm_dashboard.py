import streamlit as st

st.set_page_config(page_title="Pre-Sales CRM", layout="wide")

# LOGIN CHECK
if "user" not in st.session_state:
    st.switch_page("pages/0_Login.py")

params = st.query_params

if params.get("page") == "lead_profile":
    st.switch_page("pages/4_Lead_Profile.py")

st.title("📞 Pre-Sales CRM")
st.markdown("Use the sidebar to navigate between pages.")
