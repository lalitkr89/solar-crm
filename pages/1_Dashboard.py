import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

if "user" not in st.session_state:
    st.switch_page("pages/0_Login.py")

# ---------------- SESSION ----------------

if "selected_lead" not in st.session_state:
    st.session_state.selected_lead = None

# ---------------- SUPABASE ----------------

SUPABASE_URL = "https://pwtlcixcykpqfjlhyzxv.supabase.co"
SUPABASE_KEY = "sb_publishable_LMC-zFPQqTFA5dptZA5SXQ_ij7T1TVJ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Pre-Sales CRM", layout="wide")

st.title("📊 Pre-Sales CRM")
st.caption(f"👤 Logged in as: {st.session_state.user['name']}")

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

    users_df = users_df.rename(columns={"name": "caller_name"})

    df = df.merge(
        users_df[["id", "caller_name"]],
        left_on="assigned_to",
        right_on="id",
        how="left",
    )

    df.rename(columns={"caller_name": "assigned_caller"}, inplace=True)

if "assigned_caller" not in df.columns:
    df["assigned_caller"] = "Unassigned"

# ---------------- SEARCH ----------------

search_query = st.text_input("🔎 Global Lead Search")

filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df["phone"].astype(str).str.contains(search_query, case=False)
        | filtered_df["name"].astype(str).str.contains(search_query, case=False)
        | filtered_df["city"].astype(str).str.contains(search_query, case=False)
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

# ---------------- POWER DIALER ----------------

st.markdown("---")

if st.button("🚀 Start Calling", use_container_width=True):

    now = datetime.now()

    callback_lead = (
        supabase.table("leads")
        .select("*")
        .eq("lead_status", "open")
        .lte("callback_date", now.date().isoformat())
        .limit(1)
        .execute()
    )

    if callback_lead.data:

        st.session_state.selected_lead = callback_lead.data[0]["phone"]

        st.switch_page("pages/4_Lead_Profile.py")

    else:
        st.warning("No leads available for calling")

# ---------------- GRID ----------------

st.markdown("### 📋 Leads")

grid_df = filtered_df[
    ["name", "phone", "city", "disposition", "assigned_caller", "remarks"]
].copy()

# ADD EDIT COLUMN
grid_df.insert(0, "Edit", "Edit")

# COLUMN ORDER
grid_df.columns = [
    "🔍 Edit",
    "👤 Client",
    "📞 Phone",
    "📍 City",
    "📋 Disposition",
    "👨 Caller",
    "📝 Remarks",
]

# ---------------- BUTTON RENDERER ----------------

button_renderer = JsCode(
    """
class BtnCellRenderer {

  init(params) {

    this.eGui = document.createElement('button');

    this.eGui.innerHTML = 'Edit';

    this.eGui.style.backgroundColor = '#1976d2';
    this.eGui.style.color = 'white';
    this.eGui.style.border = 'none';
    this.eGui.style.padding = '4px 10px';
    this.eGui.style.borderRadius = '6px';
    this.eGui.style.cursor = 'pointer';

    this.eGui.addEventListener('click', () => {

        params.api.selectNode(params.node,true);

    });
  }

  getGui() {
    return this.eGui;
  }
}
"""
)

# ---------------- GRID BUILDER ----------------

gb = GridOptionsBuilder.from_dataframe(grid_df)

gb.configure_default_column(sortable=True, filter=True)

gb.configure_selection("single")

gb.configure_column("🔍 Edit", cellRenderer=button_renderer, width=100)

grid_options = gb.build()

# ---------------- GRID RENDER ----------------

grid_response = AgGrid(
    grid_df,
    gridOptions=grid_options,
    height=550,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
)

# ---------------- DETECT SELECTION ----------------

selected = grid_response.get("selected_rows")

if selected is not None:

    # CASE 1: selected list ho
    if isinstance(selected, list) and len(selected) > 0:
        phone = selected[0]["📞 Phone"]

        st.session_state.selected_lead = phone
        st.switch_page("pages/4_Lead_Profile.py")

    # CASE 2: selected dataframe ho
    if isinstance(selected, pd.DataFrame) and not selected.empty:
        phone = selected.iloc[0]["📞 Phone"]

        st.session_state.selected_lead = phone
        st.switch_page("pages/4_Lead_Profile.py")
