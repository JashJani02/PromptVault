import streamlit as st
from db import init_db
from pages import login, dashboard, storage

st.set_page_config(page_title="Prompt Vault", page_icon="📚", layout="wide")

# Initialize database (creates tables if they don't exist)
init_db()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

login_page = st.Page(login.render, title="Login", icon="🔐", url_path="login")
dashboard_page = st.Page(dashboard.render, title="Dashboard", icon="📊", url_path="dashboard", default=True)
storage_page = st.Page(storage.render, title="Storage", icon="🗂️", url_path="storage")

if st.session_state.logged_in:

    with st.sidebar:
        st.write(f"👋 Logged in as **{st.session_state.username}**")
        if st.button("Log out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
        st.divider()
    pg = st.navigation([dashboard_page, storage_page])
else:
   
    pg = st.navigation([login_page])

pg.run()