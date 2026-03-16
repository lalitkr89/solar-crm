import streamlit as st
import pandas as pd
import time
from core.database import supabase
from datetime import datetime, timedelta
from config.dispositions import not_connected_dispositions, connected_dispositions
from config.time_slots import TIME_SLOTS
from services.lead_service import get_lead_by_phone, update_lead

st.set_page_config(page_title="Lead Profile", layout="wide", page_icon="👤")

# ── AUTH ──────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.switch_page("pages/0_Login.py")

# ── CSS ───────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*,*::before,*::after{box-sizing:border-box;}
html,body,[class*="css"],.stApp{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem!important;padding-bottom:1rem!important;}
.stApp{background:#F0F4F8!important;}

[data-testid="stSidebar"]{background:#0B1F3A!important;border-right:none!important;box-shadow:4px 0 20px rgba(0,0,0,0.3)!important;}
[data-testid="stSidebar"] *{color:rgba(255,255,255,0.82)!important;}
[data-testid="stSidebarContent"]{padding:0!important;}
.sb-logo{padding:20px 18px 14px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:6px;display:flex;align-items:center;gap:10px;}
.sb-logo-icon{width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#0070D2,#00A1E0);display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;}
.sb-logo-title{font-size:16px;font-weight:800;color:white!important;}
.sb-logo-sub{font-size:10px;color:rgba(255,255,255,0.35)!important;margin-top:1px;}
.sb-user{margin:8px 12px 4px;padding:10px 12px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;gap:10px;}
.sb-avatar{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#0070D2,#00A1E0);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:white!important;flex-shrink:0;}
.sb-uname{font-size:12.5px;font-weight:600;color:white!important;}
.sb-urole{font-size:10.5px;color:rgba(255,255,255,0.38)!important;margin-top:1px;}
.sb-section{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:1.3px;color:rgba(255,255,255,0.28)!important;padding:16px 18px 5px;}
.sb-nav{padding:0 8px;}
.nav-link{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:9px;margin-bottom:2px;font-size:13px;font-weight:500;color:rgba(255,255,255,0.65)!important;cursor:pointer;}
.nav-link.active{background:#0070D2!important;color:white!important;font-weight:600;}
.sb-divider{height:1px;background:rgba(255,255,255,0.05);margin:8px 12px;}

.lp-header{background:white;border-radius:12px;padding:14px 20px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 1px 3px rgba(0,0,0,0.05),0 4px 12px rgba(0,0,0,0.04);border-left:4px solid #0070D2;}
.lp-name{font-size:18px;font-weight:700;color:#032D60;}
.lp-meta{font-size:12px;color:#8FA3BF;margin-top:3px;display:flex;align-items:center;gap:14px;}

.status-badge{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}
.s-conn{background:#DCFCE7;color:#14532D;border:1px solid #86EFAC;}
.s-nc{background:#FEE2E2;color:#7F1D1D;border:1px solid #FCA5A5;}
.disp-badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11.5px;font-weight:600;}

.timer-box{background:linear-gradient(135deg,#0070D2,#00A1E0);border-radius:12px;padding:14px 18px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;}
.timer-lbl{font-size:10.5px;font-weight:600;color:rgba(255,255,255,0.75);text-transform:uppercase;letter-spacing:0.8px;}
.timer-val{font-size:24px;font-weight:800;color:white;letter-spacing:-0.5px;font-variant-numeric:tabular-nums;}

.action-bar{background:white;border-radius:12px;padding:12px 16px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,0.05),0 4px 12px rgba(0,0,0,0.04);}

.info-card{background:white;border-radius:12px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,0.05),0 4px 12px rgba(0,0,0,0.04);margin-bottom:14px;height:100%;}
.ic-title{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.9px;color:#94A3B8;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #F1F5F9;}
.ic-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #F8FAFC;}
.ic-row:last-child{border-bottom:none;}
.ic-lbl{font-size:12px;color:#64748B;font-weight:500;}
.ic-val{font-size:12.5px;color:#0F172A;font-weight:600;text-align:right;max-width:55%;}

.tl-item{background:white;border-radius:10px;padding:12px 16px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,0.04);border-left:3px solid #0070D2;}
.tl-time{font-size:10.5px;color:#94A3B8;margin-bottom:3px;}
.tl-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;}
.tl-tag{font-size:10.5px;background:#EAF3FF;color:#0070D2;padding:2px 8px;border-radius:20px;font-weight:600;}

/* Buttons — all same height, no wrap */
div.stButton>button{
    border-radius:8px!important;font-weight:600!important;
    font-size:12px!important;border:none!important;
    transition:all 0.18s!important;
    height:36px!important;
    min-height:36px!important;
    max-height:36px!important;
    padding:0 8px!important;
    white-space:nowrap!important;
    line-height:36px!important;
}
div.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 4px 12px rgba(0,0,0,0.12)!important;}
.btn-blue div.stButton>button{background:#0070D2!important;color:white!important;}
.btn-outline div.stButton>button{background:white!important;color:#374151!important;border:1.5px solid #D1D5DB!important;}
/* Link buttons — force same height */
a[data-testid="stLinkButton"]>button{
    border-radius:8px!important;font-size:12px!important;
    font-weight:600!important;
    height:36px!important;
    min-height:36px!important;
    max-height:36px!important;
    padding:0 8px!important;
    white-space:nowrap!important;
    line-height:36px!important;
    border:1.5px solid #D1D5DB!important;
    background:white!important;
    color:#374151!important;
}
/* Tighten column gaps */
[data-testid="stHorizontalBlock"]{gap:4px!important;align-items:center!important;}
[data-testid="stHorizontalBlock"]>div{padding:0 2px!important;}
</style>
""",
    unsafe_allow_html=True,
)

# ── SESSION ───────────────────────────────────────────────────
phone = st.session_state.get("selected_lead")
if not phone:
    st.warning("No lead selected")
    if st.button("← Back to Dashboard"):
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

if "show_history" not in st.session_state:
    st.session_state.show_history = False
if "lead_start_time" not in st.session_state:
    st.session_state.lead_start_time = time.time()


# ── ACTIVITY LOG ──────────────────────────────────────────────
def log_activity(lead_id, action, field=None, old=None, new=None):
    try:
        supabase.table("lead_history").insert(
            {
                "lead_id": lead_id,
                "action": action,
                "updated_field": field,
                "old_value": str(old) if old is not None else None,
                "new_value": str(new) if new is not None else None,
                "updated_by": st.session_state.user.get("name", "Unknown"),
            }
        ).execute()
    except Exception:
        pass


# ── FETCH ─────────────────────────────────────────────────────
lead = get_lead_by_phone(phone)
if not lead:
    st.warning("Lead not found")
    if st.button("← Back"):
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

# ── SIDEBAR ───────────────────────────────────────────────────
user_name = st.session_state.user.get("name", "User")
user_initial = user_name[0].upper()

with st.sidebar:
    st.markdown(
        f"""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
    <div class="sb-logo">
        <div class="sb-logo-icon">⚡</div>
        <div><div class="sb-logo-title">SolarCRM</div><div class="sb-logo-sub">Pre-Sales Platform</div></div>
    </div>
    <div class="sb-user">
        <div class="sb-avatar">{user_initial}</div>
        <div><div class="sb-uname">{user_name}</div><div class="sb-urole">{st.session_state.user.get('role','Agent').title()}</div></div>
    </div>
    <div class="sb-section">Main Menu</div>
    <div class="sb-nav">
        <div class="nav-link">&#128202; Dashboard</div>
        <div class="nav-link">&#128100; Add Lead</div>
        <div class="nav-link">&#128197; Today's Actions</div>
        <div class="nav-link active">&#128100; Lead Profile</div>
    </div>
    <div class="sb-divider"></div>
    <div class="sb-section">Tools</div>
    <div class="sb-nav">
        <div class="nav-link">&#128194; Bulk Upload</div>
        <div class="nav-link">&#128222; Power Dialer</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ── EDIT DIALOG ───────────────────────────────────────────────
@st.dialog("✏️ Edit Lead", width="large")
def edit_lead_dialog(lead):
    from components.lead_form import lead_form

    lead_form()


# ── HELPERS ───────────────────────────────────────────────────
def ir(lbl, val):
    v = str(val) if val else "-"
    return f'<div class="ic-row"><span class="ic-lbl">{lbl}</span><span class="ic-val">{v}</span></div>'


def disp_css(val):
    if not val:
        return "background:#F1F5F9;color:#475569;border:1px solid #CBD5E1"
    if "Meeting" in val:
        return "background:#DCFCE7;color:#14532D;border:1px solid #86EFAC"
    if "Not Connected" in val:
        return "background:#FEE2E2;color:#7F1D1D;border:1px solid #FCA5A5"
    if "Call Later" in val:
        return "background:#DBEAFE;color:#1E3A8A;border:1px solid #93C5FD"
    if "Non Qualified" in val:
        return "background:#F1F5F9;color:#475569;border:1px solid #CBD5E1"
    if "Not Interested" in val:
        return "background:#F8FAFC;color:#64748B;border:1px solid #E2E8F0"
    if "Commercial" in val:
        return "background:#EDE9FE;color:#4C1D95;border:1px solid #C4B5FD"
    return "background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE"


disp_val = lead.get("disposition", "") or ""
cs_val = lead.get("call_status", "") or ""
cs_cls = "s-conn" if cs_val == "Connected" else "s-nc"

# ── HEADER ────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="lp-header">
    <div>
        <div class="lp-name">👤 {lead.get('name','-')}</div>
        <div class="lp-meta">
            <span>🏷️ {lead.get('lead_id','-') or '-'}</span>
            <span>📱 {lead.get('phone','-')}</span>
            <span>📍 {lead.get('city','-') or '-'}</span>
            <span>📅 {str(lead.get('created_at','-'))[:10]}</span>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <span class="status-badge {cs_cls}">● {cs_val or 'Unknown'}</span>
        <span class="disp-badge" style="{disp_css(disp_val)}">{disp_val[:35]+'…' if len(disp_val)>35 else disp_val or 'No Disposition'}</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── TIMER + ACTIONS ───────────────────────────────────────────
time_spent = int(time.time() - st.session_state.lead_start_time)
mins, secs = divmod(time_spent, 60)

t_col, a_col = st.columns([1, 4])

with t_col:
    st.markdown(
        f"""
    <div class="timer-box">
        <div>
            <div class="timer-lbl">Time on Lead</div>
            <div class="timer-val">{mins:02d}:{secs:02d}</div>
        </div>
        <div style="font-size:26px;opacity:0.25;">⏱</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with a_col:
    st.markdown('<div class="action-bar">', unsafe_allow_html=True)
    phone_number = lead.get("phone", "")
    b1, b2, b3, b4, b5, b6 = st.columns([1, 1, 1, 1, 1.2, 1.4])

    with b1:
        st.link_button("📞 Call", f"tel:{phone_number}", use_container_width=True)
    with b2:
        st.link_button(
            "💬 WA", f"https://wa.me/91{phone_number}", use_container_width=True
        )
    with b3:
        st.link_button(
            "📍 Map",
            f"https://maps.google.com/?q={lead.get('city','')}",
            use_container_width=True,
        )
    with b4:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.lf_phone_val = phone_number
            st.session_state.lf_last_phone = ""
            edit_lead_dialog(lead)
        st.markdown("</div>", unsafe_allow_html=True)
    with b5:
        st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
        if st.button(
            "❌ Hide" if st.session_state.show_history else "📜 History",
            use_container_width=True,
        ):
            st.session_state.show_history = not st.session_state.show_history
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with b6:
        st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
        if st.button("← Dashboard", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── INFO CARDS ────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"""
    <div class="info-card">
        <div class="ic-title">📞 Contact Details</div>
        {ir("Phone",        lead.get("phone"))}
        {ir("Alternate",    lead.get("alternate_phone"))}
        {ir("Email",        lead.get("email"))}
        {ir("City",         lead.get("city"))}
        {ir("Pincode",      lead.get("pincode"))}
        {ir("Lead Source",  lead.get("lead_source"))}
        {ir("Referred By",  lead.get("referral_type"))}
        {ir("Referrer",     lead.get("referral_name"))}
    </div>
    """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
    <div class="info-card">
        <div class="ic-title">🏠 Property & Electricity</div>
        {ir("Property Type",    lead.get("property_type"))}
        {ir("Ownership",        lead.get("ownership"))}
        {ir("Roof Type",        lead.get("roof_type"))}
        {ir("Roof Area",        f"{lead.get('roof_area')} sqft" if lead.get("roof_area") else None)}
        {ir("Sanctioned Load",  f"{lead.get('sanctioned_load')} kW" if lead.get("sanctioned_load") else None)}
        {ir("Monthly Bill",     f"₹ {lead.get('monthly_bill')}" if lead.get("monthly_bill") else None)}
        {ir("Units/Month",      f"{lead.get('units_per_month')} kWh" if lead.get("units_per_month") else None)}
    </div>
    """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
    <div class="info-card">
        <div class="ic-title">📋 Call Details</div>
        {ir("Caller",           lead.get("assigned_to"))}
        {ir("Calling Date",     lead.get("calling_date"))}
        {ir("Callback Date",    lead.get("callback_date"))}
        {ir("Callback Slot",    lead.get("callback_slot"))}
        {ir("Meeting Date",     lead.get("meeting_date"))}
        {ir("Meeting Slot",     lead.get("meeting_slot"))}
        {ir("Lead Status",      lead.get("lead_status"))}
    </div>
    """,
        unsafe_allow_html=True,
    )

# Remarks card
if lead.get("remarks"):
    st.markdown(
        f"""
    <div class="info-card">
        <div class="ic-title">📝 Remarks</div>
        <div style="font-size:13px;color:#374151;line-height:1.7;">{lead.get('remarks')}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ── TIMELINE ──────────────────────────────────────────────────
if st.session_state.show_history:
    st.markdown(
        """
    <div style="font-size:15px;font-weight:700;color:#032D60;margin:6px 0 12px;">
        📜 Activity Timeline
    </div>
    """,
        unsafe_allow_html=True,
    )

    try:
        history_res = (
            supabase.table("lead_history")
            .select("*")
            .eq("lead_id", lead["id"])
            .order("updated_at", desc=True)
            .execute()
        )

        hdf = pd.DataFrame(history_res.data)

        if hdf.empty:
            st.info("No activity recorded yet.")
        else:
            hdf["updated_at"] = (
                pd.to_datetime(hdf["updated_at"])
                .dt.tz_localize("UTC")
                .dt.tz_convert("Asia/Kolkata")
            )
            for _, h in hdf.iterrows():
                old_v = h.get("old_value", "") or ""
                new_v = h.get("new_value", "") or ""
                field = h.get("updated_field", "") or ""
                action = h.get("action", "-") or "-"
                user = h.get("updated_by", "-") or "-"
                ts = h["updated_at"].strftime("%d %b %Y • %I:%M %p")

                st.markdown(
                    f"""
                <div class="tl-item">
                    <div class="tl-time">{ts}</div>
                    <div class="tl-header">
                        <span style="font-size:12px;font-weight:600;color:#032D60;">👤 {user} &nbsp;·&nbsp; <span style="color:#0070D2;">{action}</span></span>
                        <span class="tl-tag">{field}</span>
                    </div>
                    <div style="font-size:12px;color:#374151;margin-top:4px;">
                        <span style="color:#DC2626;text-decoration:line-through;">{old_v[:60]}</span>
                        &nbsp;→&nbsp;
                        <span style="color:#16A34A;font-weight:600;">{new_v[:60]}</span>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
    except Exception as e:
        st.error(f"Error: {e}")
