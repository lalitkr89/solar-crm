import streamlit as st
from datetime import datetime
from core.database import supabase
from config.dispositions import not_connected_dispositions, connected_dispositions
from config.time_slots import TIME_SLOTS
from utils.phone_utils import clean_phone
from services.caller_service import get_caller_names, get_next_caller_dynamic
from services.lead_service import save_lead, get_lead_by_phone

LEAD_SOURCES = ["Referral", "Website", "Campaign", "Walk-in", "Cold Call", "Other"]
PROPERTY_TYPES = ["Residential", "Commercial", "Industrial", "Agricultural"]
ROOF_TYPES = ["RCC Flat", "RCC", "Sloped (Tile)", "Sloped (Metal)", "Asbestos", "Other"]
OWNERSHIP_TYPES = ["Owned", "Rented", "Leased"]
REFERRAL_TYPES = ["Existing Customer", "SolarPro", "Employee", "Other"]


# ── @st.fragment wraps the ENTIRE form so only form reruns ───
# This is defined at MODULE level (not inside dialog) — critical!
@st.fragment
def _form_fragment():

    st.markdown(
        """
    <style>
    div[data-testid="stVerticalBlock"] label,
    div[data-testid="stHorizontalBlock"] label {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        height: auto !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #374151 !important;
        margin-bottom: 3px !important;
    }
    .fs { font-size:10.5px; font-weight:700; text-transform:uppercase;
          letter-spacing:0.8px; color:#0070D2; padding:8px 0 5px;
          border-bottom:1.5px solid #EAF3FF; margin-bottom:8px; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ── Session init ──────────────────────────────────────────
    logged_in = st.session_state.get("user", {}).get("name", "")
    user_team = st.session_state.get("user", {}).get("team", "pre-sales")
    all_callers = get_caller_names(team=user_team)
    if not all_callers:
        all_callers = get_caller_names()  # fallback — all teams

    # Set defaults once — not on every rerun
    for k, v in {
        "lf_last_phone": "",
        "lf_existing": None,
        "lf_call_status": "Select Status",
        "lf_disposition": "Select Disposition",
        "lf_phone_val": "",
        "lf_name": "",
        "lf_alt": "",
        "lf_email": "",
        "lf_city": "",
        "lf_pin": "",
        "lf_rem": "",
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Caller — ALWAYS prefill with logged_in user (override every time)
    st.session_state.lf_caller = (
        logged_in
        if logged_in in all_callers
        else (all_callers[0] if all_callers else "Select Caller")
    )

    # ── PHONE ─────────────────────────────────────────────────

    def _on_phone():
        st.session_state.lf_phone_val = st.session_state.get("_lf_phone_inp", "")

    st.text_input(
        "📱 Primary Phone *",
        value=st.session_state.lf_phone_val,
        placeholder="10 digit mobile number",
        key="_lf_phone_inp",
        on_change=_on_phone,
    )

    phone = clean_phone(st.session_state.lf_phone_val)

    if phone and (not phone.isdigit() or len(phone) != 10):
        st.warning("⚠ Enter valid 10 digit number")

    # DB call ONLY when phone changes to a new valid number
    if phone.isdigit() and len(phone) == 10:
        if phone != st.session_state.lf_last_phone:
            with st.spinner("Looking up..."):
                st.session_state.lf_last_phone = phone
                st.session_state.lf_existing = get_lead_by_phone(phone)
                ld = st.session_state.lf_existing or {}
                # Store ALL field values in session_state so they persist on rerun
                st.session_state.lf_call_status = ld.get("call_status", "Select Status")
                st.session_state.lf_disposition = ld.get(
                    "disposition", "Select Disposition"
                )
                st.session_state.lf_name = ld.get("name", "")
                st.session_state.lf_alt = ld.get("alternate_phone", "") or ""
                st.session_state.lf_email = ld.get("email", "") or ""
                st.session_state.lf_city = ld.get("city", "")
                st.session_state.lf_pin = ld.get("pincode", "") or ""
                st.session_state.lf_rem = ld.get("remarks", "") or ""
                # Caller — keep logged_in as default, don't override
                if ld and logged_in not in all_callers:
                    st.session_state.lf_caller = ld.get("assigned_to", "Select Caller")
    elif not phone:
        if st.session_state.lf_last_phone:
            st.session_state.lf_last_phone = ""
            st.session_state.lf_existing = None
            st.session_state.lf_call_status = "Select Status"
            st.session_state.lf_disposition = "Select Disposition"
            st.session_state.lf_name = ""
            st.session_state.lf_alt = ""
            st.session_state.lf_email = ""
            st.session_state.lf_city = ""
            st.session_state.lf_pin = ""
            st.session_state.lf_rem = ""

    ex = st.session_state.lf_existing or {}
    if ex:
        st.info(f"✏️ Editing: **{ex.get('name','')}**")

    # ── 2 COLUMN LAYOUT ──────────────────────────────────────
    L, R = st.columns(2)

    with L:
        # Contact
        st.markdown('<div class="fs">📞 Contact</div>', unsafe_allow_html=True)
        name = st.text_input(
            "Full Name *",
            value=st.session_state.get("lf_name", ""),
            placeholder="Ramesh Gupta",
            key="lf_name",
        )
        alt_phone = st.text_input(
            "Alternate Phone",
            value=st.session_state.get("lf_alt", ""),
            placeholder="Optional",
            key="lf_alt",
        )
        email = st.text_input(
            "Email",
            value=st.session_state.get("lf_email", ""),
            placeholder="Optional",
            key="lf_email",
        )
        c1, c2 = st.columns(2)
        with c1:
            city = st.text_input(
                "City *",
                value=st.session_state.get("lf_city", ""),
                placeholder="Delhi",
                key="lf_city",
            )
        with c2:
            pincode = st.text_input(
                "Pincode",
                value=st.session_state.get("lf_pin", ""),
                placeholder="110001",
                key="lf_pin",
            )

        ls_def = ex.get("lead_source")
        lead_source = st.selectbox(
            "Lead Source",
            ["Select"] + LEAD_SOURCES,
            index=(LEAD_SOURCES.index(ls_def) + 1) if ls_def in LEAD_SOURCES else 0,
            key="lf_src",
        )

        referral_type = referral_id = referral_name = None
        if lead_source == "Referral":
            rt_def = ex.get("referral_type")
            referral_type = st.selectbox(
                "Referred By",
                ["Select"] + REFERRAL_TYPES,
                index=(
                    (REFERRAL_TYPES.index(rt_def) + 1)
                    if rt_def in REFERRAL_TYPES
                    else 0
                ),
                key="lf_rtype",
            )
            referral_name = st.text_input(
                "Referrer Name", value=ex.get("referral_name", "") or "", key="lf_rname"
            )
            if referral_type in ["Existing Customer", "SolarPro"]:
                lbl = (
                    "Order ID" if referral_type == "Existing Customer" else "Partner ID"
                )
                referral_id = st.text_input(
                    lbl, value=ex.get("referral_id", "") or "", key="lf_rid"
                )

        # Property
        st.markdown('<div class="fs">🏠 Property</div>', unsafe_allow_html=True)
        pt_def = ex.get("property_type")
        ow_def = ex.get("ownership")
        rf_def = ex.get("roof_type")
        property_type = st.selectbox(
            "Property Type",
            ["Select"] + PROPERTY_TYPES,
            index=(PROPERTY_TYPES.index(pt_def) + 1) if pt_def in PROPERTY_TYPES else 0,
            key="lf_pt",
        )
        ownership = st.selectbox(
            "Ownership",
            ["Select"] + OWNERSHIP_TYPES,
            index=(
                (OWNERSHIP_TYPES.index(ow_def) + 1) if ow_def in OWNERSHIP_TYPES else 0
            ),
            key="lf_own",
        )
        roof_type = st.selectbox(
            "Roof Type",
            ["Select"] + ROOF_TYPES,
            index=(ROOF_TYPES.index(rf_def) + 1) if rf_def in ROOF_TYPES else 0,
            key="lf_roof",
        )
        roof_area = st.number_input(
            "Roof Area (sqft)",
            min_value=0,
            value=int(ex.get("roof_area") or 0),
            step=50,
            key="lf_area",
        )

    with R:
        # Electricity
        st.markdown('<div class="fs">⚡ Electricity</div>', unsafe_allow_html=True)
        sanctioned_load = st.number_input(
            "Sanctioned Load (kW)",
            min_value=0.0,
            value=float(ex.get("sanctioned_load") or 0),
            step=0.5,
            key="lf_sl",
        )
        monthly_bill = st.number_input(
            "Monthly Bill (₹)",
            min_value=0.0,
            value=float(ex.get("monthly_bill") or 0),
            step=100.0,
            key="lf_mb",
        )
        units_per_month = st.number_input(
            "Units/Month (kWh)",
            min_value=0.0,
            value=float(ex.get("units_per_month") or 0),
            step=10.0,
            key="lf_upm",
        )

        # Call Details
        st.markdown('<div class="fs">📋 Call Details</div>', unsafe_allow_html=True)

        status_options = ["Select Status", "Not Connected", "Connected"]

        def _on_cs():
            st.session_state.lf_call_status = st.session_state._lf_cs_inp
            st.session_state.lf_disposition = "Select Disposition"

        st.selectbox(
            "Call Status *",
            status_options,
            index=(
                status_options.index(st.session_state.lf_call_status)
                if st.session_state.lf_call_status in status_options
                else 0
            ),
            key="_lf_cs_inp",
            on_change=_on_cs,
        )
        call_status = st.session_state.lf_call_status

        # Caller — prefilled with logged_in user
        def _on_caller():
            st.session_state.lf_caller = st.session_state._lf_caller_inp

        city_val = st.session_state.get("lf_city", "")
        if city_val and city_val.lower() in ["kanpur", "lucknow"]:
            assigned_caller = get_next_caller_dynamic(team=user_team)
            st.success(f"Auto → {assigned_caller}")
        else:
            cal_opts = (
                all_callers
                if logged_in in all_callers
                else ["Select Caller"] + all_callers
            )
            cur_caller = st.session_state.lf_caller
            cal_idx = cal_opts.index(cur_caller) if cur_caller in cal_opts else 0
            st.selectbox(
                "Assign Caller *",
                cal_opts,
                index=cal_idx,
                key="_lf_caller_inp",
                on_change=_on_caller,
            )
            assigned_caller = st.session_state.lf_caller

        # Disposition — on_change stores value instantly
        def _on_disp():
            st.session_state.lf_disposition = st.session_state.get(
                "_lf_disp_inp", "Select Disposition"
            )

        disposition = None
        if call_status == "Not Connected":
            nc_opts = ["Select Disposition"] + not_connected_dispositions
            cur_d = st.session_state.lf_disposition
            nc_idx = nc_opts.index(cur_d) if cur_d in nc_opts else 0
            st.selectbox(
                "Disposition *",
                nc_opts,
                index=nc_idx,
                key="_lf_disp_inp",
                on_change=_on_disp,
            )
            disposition = st.session_state.lf_disposition

        elif call_status == "Connected":
            c_opts = ["Select Disposition"] + connected_dispositions
            cur_d = st.session_state.lf_disposition
            c_idx = c_opts.index(cur_d) if cur_d in c_opts else 0
            st.selectbox(
                "Disposition *",
                c_opts,
                index=c_idx,
                key="_lf_disp_inp",
                on_change=_on_disp,
            )
            disposition = st.session_state.lf_disposition

        # Meeting
        meeting_date = meeting_slot = meeting_address = None
        if call_status == "Connected" and disposition == "Meeting Scheduled (BD)":
            st.markdown("**📅 Meeting**")
            meeting_date = st.date_input("Date", key="lf_md").isoformat()
            meeting_slot = st.selectbox("Slot", TIME_SLOTS, key="lf_ms")
            meeting_address = st.text_area("Address", key="lf_madd", height=60)

        # Callback
        callback_date = callback_slot = None
        if call_status == "Connected" and disposition and "Call Later" in disposition:
            st.markdown("**⏳ Callback**")
            callback_date = st.date_input("Date", key="lf_cbd").isoformat()
            callback_slot = st.selectbox("Slot", TIME_SLOTS, key="lf_cbs")

        # Remarks
        st.markdown('<div class="fs">📝 Remarks</div>', unsafe_allow_html=True)
        remarks = st.text_area(
            "",
            value=ex.get("remarks", "") or "",
            placeholder="Any additional notes...",
            key="lf_rem",
            height=80,
        )

    # ── SAVE — full width ─────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button(
        "💾  Save Lead", use_container_width=True, type="primary", key="lf_save"
    ):
        caller_val = st.session_state.get("lf_caller", "Select Caller")

        if not phone.isdigit() or len(phone) != 10:
            st.error("Enter valid 10 digit phone")
            st.stop()
        if not name:
            st.error("Full Name required")
            st.stop()
        if call_status == "Select Status":
            st.error("Select Call Status")
            st.stop()
        if not caller_val or caller_val == "Select Caller":
            st.error("Select Caller")
            st.stop()
        if not disposition or disposition == "Select Disposition":
            st.error("Select Disposition")
            st.stop()

        data = {
            "name": name,
            "phone": phone,
            "alternate_phone": alt_phone or None,
            "email": email or None,
            "city": city,
            "pincode": pincode or None,
            "lead_source": lead_source if lead_source != "Select" else None,
            "referral_type": (
                referral_type if referral_type and referral_type != "Select" else None
            ),
            "referral_name": referral_name or None,
            "referral_id": referral_id or None,
            "property_type": property_type if property_type != "Select" else None,
            "roof_type": roof_type if roof_type != "Select" else None,
            "roof_area": roof_area if roof_area > 0 else None,
            "ownership": ownership if ownership != "Select" else None,
            "sanctioned_load": sanctioned_load if sanctioned_load > 0 else None,
            "monthly_bill": monthly_bill if monthly_bill > 0 else None,
            "units_per_month": units_per_month if units_per_month > 0 else None,
            "call_status": call_status,
            "disposition": disposition,
            "meeting_date": meeting_date,
            "meeting_slot": meeting_slot,
            "meeting_address": meeting_address,
            "callback_date": callback_date,
            "callback_slot": callback_slot,
            "assigned_to": caller_val,
            "remarks": st.session_state.get("lf_rem", ""),
            "calling_date": datetime.now().date().isoformat(),
            "created_at": datetime.now().isoformat(),
            "lead_status": "open",
        }

        response = save_lead(data)
        if response:
            lead_db_id = response[0]["id"]
            lead_display_id = response[0].get("lead_id", "")
            old_data = st.session_state.lf_existing

            if old_data:
                for field in data:
                    ov = str(old_data.get(field))
                    nv = str(data.get(field))
                    if ov != nv:
                        supabase.table("lead_history").insert(
                            {
                                "lead_id": lead_db_id,
                                "updated_field": field,
                                "old_value": ov,
                                "new_value": nv,
                            }
                        ).execute()

            st.session_state.lf_last_phone = ""
            st.session_state.lf_existing = None
            st.session_state.lf_call_status = "Select Status"
            st.session_state.lf_phone_val = ""
            st.success(f"✅ Saved! ID: **{lead_display_id}**")
            st.rerun()


def lead_form():
    """Entry point — called from dialog or anywhere"""
    _form_fragment()
