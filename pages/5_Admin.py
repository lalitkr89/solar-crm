import streamlit as st
import pandas as pd
from core.database import supabase
from services.caller_service import clear_callers_cache

st.set_page_config(page_title="Admin Panel", layout="wide", page_icon="⚙️")

# ── AUTH CHECK ────────────────────────────────────────────────
if "user" not in st.session_state:
    st.switch_page("pages/0_Login.py")

user = st.session_state.user
if user.get("role") not in ["admin", "manager"]:
    st.error("❌ Access Denied — Admin or Manager only")
    st.stop()

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; }
.stApp { background: #F0F4F8 !important; }

.page-header {
    background: white; border-radius: 12px; padding: 16px 22px;
    margin-bottom: 20px; border-left: 4px solid #0070D2;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    display: flex; align-items: center; justify-content: space-between;
}
.page-title { font-size: 18px; font-weight: 700; color: #032D60; }
.page-sub   { font-size: 12px; color: #8FA3BF; margin-top: 2px; }

.role-badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600;
}
.role-admin   { background:#FEE2E2; color:#7F1D1D; }
.role-manager { background:#FEF3C7; color:#78350F; }
.role-agent   { background:#DCFCE7; color:#14532D; }

div.stButton > button {
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 13px !important; border: none !important;
    transition: all 0.18s !important;
}
.stTextInput label, .stSelectbox label { 
    font-size: 12.5px !important; font-weight: 600 !important; color: #374151 !important;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
    <div>
        <div class="page-title">⚙️ User Management</div>
        <div class="page-sub">Manage team members, roles and access</div>
    </div>
    <div style="font-size:12px;color:#64748B;">
        Logged in as: <strong>{user.get('name')}</strong> 
        ({user.get('role','agent').title()})
    </div>
</div>
""", unsafe_allow_html=True)

# ── FETCH USERS ───────────────────────────────────────────────
def fetch_users():
    res = supabase.table("users").select("*").order("name").execute()
    return res.data if res.data else []

# ── TABS ──────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["👥 All Users", "➕ Add New User"])

# ════════════════════════════════════════
# TAB 1 — ALL USERS
# ════════════════════════════════════════
with tab1:
    users = fetch_users()

    if not users:
        st.info("No users found.")
    else:
        # Filter by team (managers can only see their team)
        if user.get("role") == "manager":
            users = [u for u in users if u.get("team") == user.get("team")]

        st.markdown(f"**{len(users)} users** in system")
        st.markdown("")

        for u in users:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2.5, 1.5, 1.5, 1, 1])

                with col1:
                    role  = u.get("role", "agent")
                    badge = f'<span class="role-badge role-{role}">{role.title()}</span>'
                    st.markdown(f"**{u.get('name','')}** {badge} &nbsp; `{u.get('email','')}`",
                                unsafe_allow_html=True)
                with col2:
                    st.caption(f"Team: {u.get('team','pre-sales').title()}")
                with col3:
                    status = "🟢 Active" if u.get("is_active", True) else "🔴 Inactive"
                    st.caption(status)
                with col4:
                    if st.button("✏️ Edit", key=f"edit_{u['id']}"):
                        st.session_state.editing_user = u
                        st.rerun()
                with col5:
                    # Admin can deactivate, but not self
                    if user.get("role") == "admin" and u["id"] != user["id"]:
                        btn_label = "🔴 Deactivate" if u.get("is_active", True) else "🟢 Activate"
                        if st.button(btn_label, key=f"toggle_{u['id']}"):
                            supabase.table("users").update(
                                {"is_active": not u.get("is_active", True)}
                            ).eq("id", u["id"]).execute()
                            clear_callers_cache()
                            st.rerun()

                st.markdown('<hr style="margin:6px 0;border:none;border-top:1px solid #F1F5F9;">', 
                           unsafe_allow_html=True)

        # ── EDIT USER DIALOG ──────────────────────────────────
        if "editing_user" in st.session_state:
            eu = st.session_state.editing_user

            with st.expander(f"✏️ Editing: {eu.get('name')}", expanded=True):
                e1, e2 = st.columns(2)
                with e1:
                    new_name = st.text_input("Name", value=eu.get("name",""), key="eu_name")
                    new_email = st.text_input("Email", value=eu.get("email",""), key="eu_email")
                    new_password = st.text_input("New Password", type="password",
                        placeholder="Leave blank to keep same", key="eu_pass")
                with e2:
                    role_opts  = ["agent", "manager", "admin"]
                    team_opts  = ["pre-sales", "sales", "bd"]
                    cur_role   = eu.get("role", "agent")
                    cur_team   = eu.get("team", "pre-sales")

                    # Managers can only set agent role for their team
                    if user.get("role") == "manager":
                        role_opts = ["agent"]
                        team_opts = [user.get("team", "pre-sales")]

                    new_role = st.selectbox("Role", role_opts,
                        index=role_opts.index(cur_role) if cur_role in role_opts else 0,
                        key="eu_role")
                    new_team = st.selectbox("Team", team_opts,
                        index=team_opts.index(cur_team) if cur_team in team_opts else 0,
                        key="eu_team")

                s1, s2 = st.columns(2)
                with s1:
                    if st.button("💾 Save Changes", use_container_width=True, type="primary", key="eu_save"):
                        update_data = {
                            "name":  new_name,
                            "email": new_email,
                            "role":  new_role,
                            "team":  new_team,
                        }
                        if new_password:
                            update_data["password"] = new_password

                        supabase.table("users").update(update_data).eq("id", eu["id"]).execute()
                        clear_callers_cache()
                        del st.session_state.editing_user
                        st.success("✅ User updated!")
                        st.rerun()
                with s2:
                    if st.button("✕ Cancel", use_container_width=True, key="eu_cancel"):
                        del st.session_state.editing_user
                        st.rerun()

# ════════════════════════════════════════
# TAB 2 — ADD NEW USER
# ════════════════════════════════════════
with tab2:
    st.markdown("#### Add New Team Member")

    a1, a2 = st.columns(2)
    with a1:
        new_name     = st.text_input("Full Name *", placeholder="Ravi Kumar", key="nu_name")
        new_email    = st.text_input("Email *", placeholder="ravi@company.com", key="nu_email")
        new_password = st.text_input("Password *", type="password", key="nu_pass")
    with a2:
        role_options = ["agent", "manager", "admin"] if user.get("role") == "admin" else ["agent"]
        team_options = ["pre-sales", "sales", "bd"] if user.get("role") == "admin" else [user.get("team","pre-sales")]

        new_role = st.selectbox("Role *", role_options, key="nu_role")
        new_team = st.selectbox("Team *", team_options, key="nu_team")

    st.markdown("")

    if st.button("➕ Add User", use_container_width=True, type="primary", key="nu_add"):
        if not new_name or not new_email or not new_password:
            st.error("Name, Email and Password required")
        else:
            # Check duplicate email
            existing = supabase.table("users").select("id").eq("email", new_email).execute()
            if existing.data:
                st.error("Email already exists!")
            else:
                supabase.table("users").insert({
                    "name":      new_name,
                    "email":     new_email,
                    "password":  new_password,
                    "role":      new_role,
                    "team":      new_team,
                    "is_active": True,
                }).execute()
                clear_callers_cache()
                st.success(f"✅ {new_name} added as {new_role} in {new_team} team!")
                st.rerun()
