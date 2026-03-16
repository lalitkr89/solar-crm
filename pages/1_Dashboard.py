import streamlit as st
import pandas as pd
import time
from core.database import supabase
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from services.lead_service import get_all_leads
from services.dialer_service import get_next_lead
from components.lead_form import lead_form

# ── AUTH ──────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.switch_page("pages/0_Login.py")

if "selected_lead" not in st.session_state:
    st.session_state.selected_lead = None
if "card_filter" not in st.session_state:
    st.session_state.card_filter = None  # active card filter

st.set_page_config(
    page_title="Pre-Sales CRM",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="⚡",
)

# ================================================================
#  CSS
# ================================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*,*::before,*::after{box-sizing:border-box;}
html,body,[class*="css"],.stApp{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem!important;padding-bottom:1rem!important;}
.stApp{background:#F0F4F8!important;}

/* ── SIDEBAR ── */
[data-testid="stSidebar"]{background:#0B1F3A!important;border-right:none!important;box-shadow:4px 0 20px rgba(0,0,0,0.3)!important;}
[data-testid="stSidebar"] *{color:rgba(255,255,255,0.82)!important;}
[data-testid="stSidebarContent"]{padding:0!important;}
.sb-logo{padding:20px 18px 14px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:6px;display:flex;align-items:center;gap:10px;}
.sb-logo-icon{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#0070D2,#00A1E0);display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;}
.sb-logo-title{font-size:16px;font-weight:800;color:white!important;letter-spacing:-0.3px;}
.sb-logo-sub{font-size:10px;color:rgba(255,255,255,0.35)!important;margin-top:1px;}
.sb-user{margin:8px 12px 4px;padding:10px 12px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;gap:10px;}
.sb-avatar{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#0070D2,#00A1E0);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:white!important;flex-shrink:0;}
.sb-uname{font-size:12.5px;font-weight:600;color:white!important;}
.sb-urole{font-size:10.5px;color:rgba(255,255,255,0.38)!important;margin-top:1px;}
.sb-section{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:1.3px;color:rgba(255,255,255,0.28)!important;padding:16px 18px 5px;}
.sb-nav{padding:0 8px;}
.nav-link{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:9px;margin-bottom:2px;font-size:13px;font-weight:500;color:rgba(255,255,255,0.65)!important;cursor:pointer;transition:all 0.18s;}
.nav-link:hover{background:rgba(255,255,255,0.07)!important;color:white!important;}
.nav-link.active{background:#0070D2!important;color:white!important;font-weight:600;box-shadow:0 3px 10px rgba(0,112,210,0.4);}
.nav-link i{width:18px;text-align:center;font-size:13px;opacity:0.85;}
.nav-link.active i{opacity:1;}
.sb-divider{height:1px;background:rgba(255,255,255,0.05);margin:8px 12px;}

/* ── TOP HEADER ── */
.top-header{background:white;border-radius:12px;padding:13px 20px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 1px 3px rgba(0,0,0,0.05),0 4px 12px rgba(0,0,0,0.04);border-left:4px solid #0070D2;}
.top-header-title{font-size:18px;font-weight:700;color:#032D60;letter-spacing:-0.3px;}
.top-header-sub{font-size:11.5px;color:#8FA3BF;margin-top:2px;display:flex;align-items:center;gap:5px;}
.live-dot{display:inline-block;width:7px;height:7px;background:#22C55E;border-radius:50%;animation:pulse 2s infinite;}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(34,197,94,0.5);}70%{box-shadow:0 0 0 5px rgba(34,197,94,0);}100%{box-shadow:0 0 0 0 rgba(34,197,94,0);}}

/* ── CLOCK BADGE ── */
.clock-badge{background:#EAF3FF;border:1px solid #C5DCF5;padding:8px 18px;border-radius:12px;text-align:center;min-width:165px;}
.clock-date{font-size:10.5px;font-weight:600;color:#0070D2;letter-spacing:0.3px;}
.clock-time{font-size:22px;font-weight:800;color:#032D60;letter-spacing:-0.5px;font-variant-numeric:tabular-nums;line-height:1.2;}

/* ── METRIC CARDS ── */
.metrics-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;}
@media(max-width:900px){.metrics-row{grid-template-columns:repeat(2,1fr);}}

.metric-card{background:white;border-radius:12px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,0.05),0 4px 12px rgba(0,0,0,0.04);display:flex;align-items:center;gap:14px;border-top:3px solid transparent;transition:box-shadow 0.22s,transform 0.22s;animation:slideUp 0.45s ease both;cursor:pointer;position:relative;}
.metric-card:hover{box-shadow:0 6px 24px rgba(0,0,0,0.12)!important;transform:translateY(-2px);}
.metric-card.active-filter{box-shadow:0 0 0 2.5px #0070D2,0 6px 20px rgba(0,112,210,0.18)!important;transform:translateY(-2px);}
.metric-card.c1{border-top-color:#0070D2;} .metric-card.c2{border-top-color:#16A34A;} .metric-card.c3{border-top-color:#D97706;} .metric-card.c4{border-top-color:#7C3AED;}
.metric-card:nth-child(1){animation-delay:0.04s;} .metric-card:nth-child(2){animation-delay:0.10s;} .metric-card:nth-child(3){animation-delay:0.16s;} .metric-card:nth-child(4){animation-delay:0.22s;}
@keyframes slideUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}

.metric-icon-box{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;}
.metric-card.c1 .metric-icon-box{background:#EAF3FF;color:#0070D2;} .metric-card.c2 .metric-icon-box{background:#DCFCE7;color:#16A34A;} .metric-card.c3 .metric-icon-box{background:#FEF3C7;color:#D97706;} .metric-card.c4 .metric-icon-box{background:#EDE9FE;color:#7C3AED;}
.metric-text{flex:1;min-width:0;}
.metric-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.9px;color:#94A3B8;margin-bottom:2px;}
.metric-value{font-size:26px;font-weight:800;line-height:1.1;letter-spacing:-1px;margin-bottom:2px;}
.metric-card.c1 .metric-value{color:#0070D2;} .metric-card.c2 .metric-value{color:#16A34A;} .metric-card.c3 .metric-value{color:#D97706;} .metric-card.c4 .metric-value{color:#7C3AED;}
.metric-footer{font-size:10.5px;color:#94A3B8;}
.trend-up{color:#16A34A;font-weight:600;}

/* click hint on cards */
.metric-card::after{content:'Click to filter';position:absolute;bottom:7px;right:10px;font-size:9px;color:#CBD5E1;font-weight:500;opacity:0;transition:opacity 0.2s;}
.metric-card:hover::after{opacity:1;}

/* active filter badge */
.filter-badge{display:inline-flex;align-items:center;gap:7px;background:#EAF3FF;border:1px solid #BFDBFE;color:#1D4ED8;padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:10px;}
.filter-badge .clear-x{cursor:pointer;color:#6B7280;font-size:13px;margin-left:2px;}
.filter-badge .clear-x:hover{color:#DC2626;}

/* ── BUTTONS ── */
div.stButton>button{border-radius:8px!important;font-weight:600!important;font-size:13px!important;border:none!important;transition:all 0.18s ease!important;height:40px!important;}
div.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 4px 12px rgba(0,0,0,0.13)!important;}
.btn-blue  div.stButton>button{background:#0070D2!important;color:white!important;}
.btn-blue  div.stButton>button:hover{background:#0060BB!important;}
.btn-green div.stButton>button{background:#16A34A!important;color:white!important;}
.btn-green div.stButton>button:hover{background:#14913F!important;}
.btn-ghost div.stButton>button{background:white!important;color:#374151!important;border:1.5px solid #D1D5DB!important;}
.btn-ghost div.stButton>button:hover{background:#F9FAFB!important;}
.btn-red   div.stButton>button{background:#FEE2E2!important;color:#DC2626!important;border:1px solid #FCA5A5!important;font-size:11px!important;height:32px!important;padding:0 10px!important;}

/* ── SEARCH ── */
.stTextInput>div>div>input{border-radius:8px!important;border:1.5px solid #D1D5DB!important;padding:9px 14px!important;font-size:13px!important;background:#F9FAFB!important;color:#111827!important;height:40px!important;transition:all 0.18s!important;}
.stTextInput>div>div>input:focus{border-color:#0070D2!important;background:white!important;box-shadow:0 0 0 3px rgba(0,112,210,0.10)!important;}
.stTextInput>div>div>input::placeholder{color:#9CA3AF!important;}
.stTextInput label{display:none!important;}

/* ── TABLE ── */
.tbl-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;}
.tbl-title{font-size:14.5px;font-weight:700;color:#0F172A;}
.tbl-badge{background:#EAF3FF;color:#0070D2;font-size:11.5px;font-weight:600;padding:3px 11px;border-radius:20px;border:1px solid #BFDBFE;}

.ag-root-wrapper{border-radius:10px!important;border:1px solid #E2E8F0!important;overflow:hidden!important;}
.ag-header{background:#0F172A!important;border-bottom:none!important;}
.ag-header-cell-label{color:rgba(255,255,255,0.80)!important;font-size:10.5px!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:0.8px!important;}
.ag-row-even{background:#FAFBFD!important;} .ag-row-odd{background:white!important;} .ag-row:hover{background:#EFF6FF!important;}
.ag-cell{font-size:13px!important;color:#1E293B!important;border-right:1px solid #F1F5F9!important;}
.ag-paging-panel{background:#F8FAFC!important;border-top:1px solid #E2E8F0!important;color:#64748B!important;font-size:11.5px!important;}

::-webkit-scrollbar{width:5px;height:5px;} ::-webkit-scrollbar-track{background:#F1F5F9;border-radius:3px;} ::-webkit-scrollbar-thumb{background:#CBD5E1;border-radius:3px;} ::-webkit-scrollbar-thumb:hover{background:#0070D2;}
</style>
""",
    unsafe_allow_html=True,
)

# ================================================================
#  SIDEBAR
# ================================================================
with st.sidebar:
    user_name = st.session_state.user.get("name", "User")
    user_initial = user_name[0].upper()
    st.markdown(
        f"""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
    <div class="sb-logo">
        <div class="sb-logo-icon">⚡</div>
        <div><div class="sb-logo-title">SolarCRM</div><div class="sb-logo-sub">Pre-Sales Platform</div></div>
    </div>
    <div class="sb-user">
        <div class="sb-avatar">{user_initial}</div>
        <div><div class="sb-uname">{user_name}</div><div class="sb-urole">Pre-Sales Agent</div></div>
    </div>
    <div class="sb-section">Main Menu</div>
    <div class="sb-nav">
        <div class="nav-link active"><i class="fa-solid fa-gauge-high"></i> Dashboard</div>
        <div class="nav-link"><i class="fa-solid fa-user-plus"></i> Add Lead</div>
        <div class="nav-link"><i class="fa-solid fa-calendar-check"></i> Today's Actions</div>
        <div class="nav-link"><i class="fa-solid fa-address-card"></i> Lead Profile</div>
    </div>
    <div class="sb-divider"></div>
    <div class="sb-section">Tools</div>
    <div class="sb-nav">
        <div class="nav-link"><i class="fa-solid fa-file-arrow-up"></i> Bulk Upload</div>
        <div class="nav-link"><i class="fa-solid fa-phone-volume"></i> Power Dialer</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>" * 4, unsafe_allow_html=True)
    st.markdown(
        '<div style="padding:8px 18px;font-size:10px;color:rgba(255,255,255,0.16);text-align:center;">SolarCRM v2.0 &nbsp;•&nbsp; Built with ❤️</div>',
        unsafe_allow_html=True,
    )

# ================================================================
#  DIALOGS
# ================================================================
# Bulk upload dialog only


@st.dialog("➕ Add / Update Lead", width="large")
def add_lead_dialog():
    lead_form()


@st.dialog("📂 Bulk Lead Upload")
def bulk_upload_dialog():
    try:
        sample = supabase.table("leads").select("*").limit(1).execute()
        columns = (
            list(sample.data[0].keys())
            if sample.data
            else ["name", "phone", "city", "call_status", "disposition", "remarks"]
        )
        columns = [
            c
            for c in columns
            if c not in ["id", "created_at", "updated_at", "lead_status"]
        ]
        st.download_button(
            "⬇ Download Template",
            pd.DataFrame(columns=columns).to_csv(index=False),
            "crm_template.csv",
            "text/csv",
        )
    except Exception as e:
        st.error("Template error")
        st.write(e)
    st.markdown("---")
    file = st.file_uploader("Upload CSV", type=["csv"])
    if file:
        df_u = pd.read_csv(file, dtype={"phone": str})
        df_u["phone"] = (
            df_u["phone"]
            .astype(str)
            .str.replace("+91", "", regex=False)
            .str.replace(" ", "")
            .str.replace("-", "")
            .str.strip()
        )
        if "disposition" in df_u.columns:
            df_u["disposition"] = (
                df_u["disposition"]
                .astype(str)
                .str.strip()
                .replace("", "New Lead")
                .fillna("New Lead")
            )
        df_u = df_u[df_u["phone"].str.len() == 10]
        if len(df_u) > 500:
            st.error("Max 500 rows")
            st.stop()
        for col in ["meeting_date", "callback_date"]:
            if col in df_u.columns:
                df_u[col] = pd.to_datetime(df_u[col], dayfirst=True, errors="coerce")
        existing_phones = {
            r["phone"] for r in supabase.table("leads").select("phone").execute().data
        }
        new_leads, updates, skipped = [], [], 0
        for _, row in df_u.iterrows():
            p = str(row["phone"])
            filled = {
                c: v
                for c, v in row.items()
                if c != "phone" and pd.notna(v) and str(v).strip() != ""
            }
            if p not in existing_phones:
                new_leads.append(row.to_dict())
            elif filled:
                updates.append((p, filled))
            else:
                skipped += 1
        c1, c2, c3 = st.columns(3)
        c1.metric("New", len(new_leads))
        c2.metric("Updates", len(updates))
        c3.metric("Skip", skipped)
        if st.button("Confirm Upload", use_container_width=True):
            ins, upd, fail = 0, 0, 0
            if new_leads:
                try:
                    supabase.table("leads").insert(new_leads).execute()
                    ins = len(new_leads)
                except:
                    fail += len(new_leads)
            for p, d in updates:
                try:
                    supabase.table("leads").update(d).eq("phone", p).execute()
                    upd += 1
                except:
                    fail += 1
            st.success(f"Done — Inserted: {ins} | Updated: {upd} | Failed: {fail}")
            st.rerun()


# ================================================================
#  FETCH DATA
# ================================================================
users_res = supabase.table("users").select("*").execute()
users_df = pd.DataFrame(users_res.data)
df = pd.DataFrame(get_all_leads())

today_label = datetime.now().strftime("%a, %d %b %Y")
today_str = datetime.now().date().isoformat()

# ================================================================
#  TOP HEADER  +  LIVE CLOCK (Python side — reliable!)
# ================================================================
header_col, clock_col = st.columns([5, 1])

with header_col:
    st.markdown(
        f"""
    <div class="top-header" style="margin-bottom:0;">
        <div>
            <div class="top-header-title">👋 Welcome, {user_name}</div>
            <div class="top-header-sub">
                <span class="live-dot"></span> Live &nbsp;&bull;&nbsp; Pre-Sales
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with clock_col:
    # Live clock placeholder — updates every second via st.empty + time.sleep loop
    clock_ph = st.empty()
    now = datetime.now()
    clock_ph.markdown(
        f"""
    <div class="clock-badge">
        <div class="clock-date">&#128197; {today_label}</div>
        <div class="clock-time">{now.strftime("%H:%M:%S")}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

# ================================================================
#  METRICS CALCULATION
# ================================================================
total_leads = connected = meetings = meetings_today = callbacks_today = connect_pct = 0

if not df.empty:
    df["meeting_date"] = pd.to_datetime(df["meeting_date"], errors="coerce")
    df["callback_date"] = pd.to_datetime(df["callback_date"], errors="coerce")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    if not users_df.empty and "assigned_to" in df.columns:
        udf = users_df.rename(columns={"name": "caller_name"})
        df = df.merge(
            udf[["id", "caller_name"]], left_on="assigned_to", right_on="id", how="left"
        )
        df.rename(columns={"caller_name": "assigned_caller"}, inplace=True)
    if "assigned_caller" not in df.columns:
        df["assigned_caller"] = "Unassigned"

    total_leads = len(df)
    connected = len(df[df["call_status"] == "Connected"])
    meetings = len(df[df["disposition"] == "Meeting Scheduled (BD)"])
    meetings_today = len(df[df["meeting_date"].astype(str).str[:10] == today_str])
    callbacks_today = len(df[df["callback_date"].astype(str).str[:10] == today_str])
    connect_pct = round(connected / total_leads * 100) if total_leads else 0

# ── Read card filter from query params (set by JS onclick) ───
qp = st.query_params
if "cf" in qp:
    val = qp["cf"]
    # toggle: same card again = clear
    if val == st.session_state.card_filter:
        st.session_state.card_filter = None
    else:
        st.session_state.card_filter = val if val != "none" else None
    st.query_params.clear()
    st.rerun()

cf = st.session_state.card_filter

c1a = "active-filter" if cf == "total" else ""
c2a = "active-filter" if cf == "connected" else ""
c3a = "active-filter" if cf == "meetings_today" else ""
c4a = "active-filter" if cf == "callbacks_today" else ""

st.markdown(
    f"""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
<div class="metrics-row">
    <div class="metric-card c1 {c1a}" onclick="setFilter('total')">
        <div class="metric-icon-box"><i class="fa-solid fa-users"></i></div>
        <div class="metric-text">
            <div class="metric-label">Total Leads</div>
            <div class="metric-value">{total_leads}</div>
            <div class="metric-footer">All time in pipeline</div>
        </div>
    </div>
    <div class="metric-card c2 {c2a}" onclick="setFilter('connected')">
        <div class="metric-icon-box"><i class="fa-solid fa-phone-flip"></i></div>
        <div class="metric-text">
            <div class="metric-label">Connected</div>
            <div class="metric-value">{connected}</div>
            <div class="metric-footer"><span class="trend-up">&#8593; {connect_pct}%</span> connect rate</div>
        </div>
    </div>
    <div class="metric-card c3 {c3a}" onclick="setFilter('meetings_today')">
        <div class="metric-icon-box"><i class="fa-solid fa-handshake"></i></div>
        <div class="metric-text">
            <div class="metric-label">Meetings Today</div>
            <div class="metric-value">{meetings_today}</div>
            <div class="metric-footer">Scheduled for today</div>
        </div>
    </div>
    <div class="metric-card c4 {c4a}" onclick="setFilter('callbacks_today')">
        <div class="metric-icon-box"><i class="fa-solid fa-clock-rotate-left"></i></div>
        <div class="metric-text">
            <div class="metric-label">Callbacks Today</div>
            <div class="metric-value">{callbacks_today}</div>
            <div class="metric-footer">Due today</div>
        </div>
    </div>
</div>

<script>
function setFilter(val) {{
    // Set query param on parent window URL then trigger Streamlit rerun
    var cur = "{cf or ''}";
    var next = (cur === val) ? "none" : val;
    // Use parent window since Streamlit runs in iframe context
    var target = window.parent ? window.parent : window;
    var base = target.location.href.split('?')[0];
    target.location.href = base + '?cf=' + next;
}}
</script>
""",
    unsafe_allow_html=True,
)

# active filter label + clear button
if cf and cf != "none":
    labels = {
        {
            "total": "All Leads",
            "connected": "Connected Leads",
            "meetings_today": "Meetings Today",
            "callbacks_today": "Callbacks Today",
        }
    }
    fcol, xcol = st.columns([4, 0.8])
    with fcol:
        st.markdown(
            f'<div class="filter-badge">&#128269; Showing: <strong>{labels.get(cf,"")}</strong></div>',
            unsafe_allow_html=True,
        )
    with xcol:
        st.markdown('<div class="btn-red">', unsafe_allow_html=True)
        if st.button("✕ Clear", key="clear_filter", use_container_width=True):
            st.session_state.card_filter = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ── TOOLBAR ──────────────────────────────────────────────────
col_s, col_a, col_b, col_d = st.columns([3.5, 0.9, 1.0, 1.1])

with col_s:
    search_query = st.text_input(
        "s",
        placeholder="🔍  Search by name, phone or city...",
        label_visibility="collapsed",
    )

with col_a:
    st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
    if st.button("＋  Add Lead", use_container_width=True):
        add_lead_dialog()
    st.markdown("</div>", unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("↑  Bulk Upload", use_container_width=True):
        bulk_upload_dialog()
    st.markdown("</div>", unsafe_allow_html=True)

with col_d:
    st.markdown('<div class="btn-green">', unsafe_allow_html=True)
    if st.button("▶  Start Calling", use_container_width=True):
        next_lead = get_next_lead()
        if next_lead:
            st.session_state.selected_lead = next_lead["phone"]
            st.switch_page("pages/4_Lead_Profile.py")
        else:
            st.warning("No leads available for calling right now.")
    st.markdown("</div>", unsafe_allow_html=True)

# ================================================================
#  LEADS TABLE
# ================================================================
if df.empty:
    st.info("No leads in the system yet.")
    st.stop()

filtered_df = df.copy()

if not cf or cf in ("total", "none"):
    pass
elif cf == "connected":
    filtered_df = filtered_df[filtered_df["call_status"] == "Connected"]
elif cf == "meetings_today":
    filtered_df = filtered_df[
        filtered_df["meeting_date"].astype(str).str[:10] == today_str
    ]
elif cf == "callbacks_today":
    filtered_df = filtered_df[
        filtered_df["callback_date"].astype(str).str[:10] == today_str
    ]

if search_query:
    filtered_df = filtered_df[
        filtered_df["phone"].astype(str).str.contains(search_query, case=False)
        | filtered_df["name"].astype(str).str.contains(search_query, case=False)
        | filtered_df["city"].astype(str).str.contains(search_query, case=False)
    ]

st.markdown(
    f"""
<div class="tbl-header">
    <div class="tbl-title">Lead Records</div>
    <div class="tbl-badge">{len(filtered_df)} records</div>
</div>
""",
    unsafe_allow_html=True,
)

grid_df = filtered_df[
    [
        "name",
        "phone",
        "city",
        "call_status",
        "disposition",
        "assigned_caller",
        "remarks",
    ]
].copy()
grid_df.columns = [
    "Name",
    "Phone",
    "City",
    "Status",
    "Disposition",
    "Caller",
    "Remarks",
]

status_renderer = JsCode(
    """
class S{init(p){this.e=document.createElement('div');this.e.style.cssText='display:flex;align-items:center;gap:7px;height:100%;';
const d=document.createElement('span'),l=document.createElement('span'),v=p.value||'';
if(v==='Connected'){d.style.cssText='width:8px;height:8px;border-radius:50%;background:#16A34A;flex-shrink:0;';l.style.cssText='font-size:12.5px;font-weight:600;color:#16A34A;';}
else{d.style.cssText='width:8px;height:8px;border-radius:50%;background:#DC2626;flex-shrink:0;';l.style.cssText='font-size:12.5px;font-weight:600;color:#DC2626;';}
l.textContent=v;this.e.appendChild(d);this.e.appendChild(l);}getGui(){return this.e;}}
"""
)

disp_renderer = JsCode(
    """
class D{init(p){this.e=document.createElement('div');this.e.style.cssText='display:flex;align-items:center;height:100%;';
const pill=document.createElement('span'),v=p.value||'';
let bg,color,border;
if(v.includes('Meeting')){bg='#DCFCE7';color='#14532D';border='#86EFAC';}
else if(v.includes('Not Connected')){bg='#FEE2E2';color='#7F1D1D';border='#FCA5A5';}
else if(v.includes('Call Later')){bg='#DBEAFE';color='#1E3A8A';border='#93C5FD';}
else if(v.includes('Non Qualified')){bg='#F1F5F9';color='#475569';border='#CBD5E1';}
else if(v.includes('Not Interested')){bg='#F8FAFC';color='#64748B';border='#E2E8F0';}
else if(v.includes('Language')){bg='#FEF9C3';color='#713F12';border='#FDE047';}
else if(v.includes('Commercial')){bg='#EDE9FE';color='#4C1D95';border='#C4B5FD';}
else if(v.includes('Housing')){bg='#FFF7ED';color='#7C2D12';border='#FDBA74';}
else{bg='#EFF6FF';color='#1D4ED8';border='#BFDBFE';}
const short=v.length>28?v.substring(0,26)+'…':v;
pill.textContent=short;pill.title=v;
pill.style.cssText='background:'+bg+';color:'+color+';border:1px solid '+border+';padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap;cursor:default;display:inline-block;';
this.e.appendChild(pill);}getGui(){return this.e;}}
"""
)

name_renderer = JsCode(
    """
class N{init(p){this.e=document.createElement('div');this.e.style.cssText='display:flex;align-items:center;gap:9px;height:100%;';
const av=document.createElement('div'),name=(p.value||'?').trim();
const ini=name.split(' ').map(w=>w[0]).join('').substring(0,2).toUpperCase();
const cols=['#0070D2','#16A34A','#7C3AED','#D97706','#DC2626','#0891B2'];
const col=cols[name.charCodeAt(0)%cols.length];
av.textContent=ini;av.style.cssText='width:29px;height:29px;border-radius:50%;background:'+col+';color:white;font-size:10.5px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;';
const txt=document.createElement('span');txt.textContent=name;txt.style.cssText='font-size:13px;font-weight:500;color:#0F172A;';
this.e.appendChild(av);this.e.appendChild(txt);}getGui(){return this.e;}}
"""
)

gb = GridOptionsBuilder.from_dataframe(grid_df)
gb.configure_default_column(sortable=True, filter=True, resizable=True)
gb.configure_selection("single")
gb.configure_column("Name", cellRenderer=name_renderer, minWidth=160)
gb.configure_column("Phone", minWidth=128)
gb.configure_column("City", minWidth=95)
gb.configure_column("Status", cellRenderer=status_renderer, minWidth=130)
gb.configure_column("Disposition", cellRenderer=disp_renderer, minWidth=210)
gb.configure_column("Caller", minWidth=110)
gb.configure_column("Remarks", minWidth=150)
gb.configure_grid_options(
    rowHeight=50,
    headerHeight=44,
    animateRows=True,
    pagination=True,
    paginationPageSize=20,
)

grid_response = AgGrid(
    grid_df,
    gridOptions=gb.build(),
    height=520,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
    theme="streamlit",
)

selected = grid_response.get("selected_rows")
if selected is not None:
    if isinstance(selected, list) and len(selected) > 0:
        st.session_state.selected_lead = selected[0]["Phone"]
        st.switch_page("pages/4_Lead_Profile.py")
    if isinstance(selected, pd.DataFrame) and not selected.empty:
        st.session_state.selected_lead = selected.iloc[0]["Phone"]
        st.switch_page("pages/4_Lead_Profile.py")
