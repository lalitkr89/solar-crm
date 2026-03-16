import os
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


@st.cache_resource
def _get_supabase_client():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Warmup — runs ONCE per app session, not on every rerun
    try:
        client.table("leads").select("id").limit(1).execute()
    except Exception:
        pass
    return client


supabase = _get_supabase_client()
