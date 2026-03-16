import streamlit as st
from core.database import supabase

st.set_page_config(page_title="SolarCRM Login", layout="centered", page_icon="⚡")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }
/* Hide sidebar toggle on login */
[data-testid="collapsedControl"] { display: none !important; }

.stApp { background: #F0F4F8 !important; }

/* ── Shrink default streamlit padding ── */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
    max-width: 420px !important;
}

/* ── TOP ACCENT BAR ── */
.topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #0070D2, #00A1E0);
    z-index: 9999;
}

/* ── BRAND ── */
.brand {
    display: flex; align-items: center;
    justify-content: center; gap: 10px;
    margin-bottom: 20px;
}
.brand-icon {
    width: 38px; height: 38px; border-radius: 10px;
    background: linear-gradient(135deg, #0070D2, #00A1E0);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; box-shadow: 0 3px 10px rgba(0,112,210,0.3);
}
.brand-name { font-size: 22px; font-weight: 800; color: #032D60; letter-spacing: -0.5px; }
.brand-pill {
    font-size: 9.5px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; color: #0070D2;
    background: #EAF3FF; border: 1px solid #BFDBFE;
    padding: 2px 7px; border-radius: 20px;
}

/* ── CARD ── */
.card {
    background: white; border-radius: 16px;
    padding: 28px 28px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05), 0 8px 30px rgba(0,0,0,0.08);
    border: 1px solid #E8EFF6;
    margin-bottom: 14px;
}
.card-title { font-size: 17px; font-weight: 700; color: #0F172A; margin-bottom: 2px; }
.card-sub   { font-size: 12.5px; color: #64748B; margin-bottom: 20px; }
.card-divider { height: 1px; background: #F1F5F9; margin-bottom: 18px; }

/* ── INPUTS ── */
.stTextInput > div > div > input {
    border-radius: 9px !important;
    border: 1.5px solid #E2E8F0 !important;
    padding: 9px 13px !important;
    font-size: 13.5px !important;
    background: #F8FAFC !important;
    color: #0F172A !important;
    transition: all 0.15s !important;
    height: 40px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #0070D2 !important;
    background: white !important;
    box-shadow: 0 0 0 3px rgba(0,112,210,0.10) !important;
}
.stTextInput > div > div > input::placeholder { color: #94A3B8 !important; }
.stTextInput label {
    font-size: 12px !important; font-weight: 600 !important; color: #374151 !important;
}
/* Reduce gap between inputs */
div[data-testid="stVerticalBlock"] > div { margin-bottom: 0 !important; }

/* ── BUTTON ── */
div.stButton > button {
    background: #0070D2 !important; color: white !important;
    border: none !important; border-radius: 9px !important;
    height: 42px !important; font-size: 14px !important;
    font-weight: 700 !important; width: 100% !important;
    box-shadow: 0 2px 8px rgba(0,112,210,0.28) !important;
    transition: all 0.15s ease !important;
    margin-top: 6px !important;
}
div.stButton > button:hover {
    background: #005BBF !important;
    box-shadow: 0 4px 14px rgba(0,112,210,0.38) !important;
    transform: translateY(-1px) !important;
}

/* ── ALERTS compact ── */
.stAlert { border-radius: 9px !important; font-size: 12.5px !important; padding: 8px 12px !important; margin-top: 8px !important; }

/* ── FOOTER ── */
.ft { text-align: center; font-size: 11px; color: #94A3B8; margin-top: 10px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="topbar"></div>', unsafe_allow_html=True)

# ── BRAND ─────────────────────────────────────────────────────
st.markdown(
    """
<div class="brand">
    <div class="brand-icon">⚡</div>
    <div class="brand-name">SolarCRM</div>
    <div class="brand-pill">Pre-Sales</div>
</div>
""",
    unsafe_allow_html=True,
)

# ── CARD HEADER ───────────────────────────────────────────────
st.markdown(
    """
<div class="card">
    <div class="card-title">Welcome back 👋</div>
    <div class="card-sub">Sign in to continue to your dashboard</div>
    <div class="card-divider"></div>
</div>
""",
    unsafe_allow_html=True,
)

# ── FORM — rendered by Streamlit directly (no scroll issue) ───
email = st.text_input("Email Address", placeholder="you@company.com")
password = st.text_input("Password", type="password", placeholder="••••••••")

if st.button("Sign In  →", use_container_width=True):
    if not email:
        st.error("Please enter your email.")
    else:
        with st.spinner(""):
            user = supabase.table("users").select("*").eq("email", email).execute()
            if user.data:
                u = user.data[0]
                if "password" in u and u["password"]:
                    if u["password"] != password:
                        st.error("❌ Incorrect password.")
                        st.stop()
                st.session_state.user = u
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.error("❌ No account found with this email.")

st.markdown(
    '<div class="ft">SolarCRM v2.0 &nbsp;•&nbsp; © 2026</div>', unsafe_allow_html=True
)
