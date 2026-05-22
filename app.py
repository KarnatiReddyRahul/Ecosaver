import streamlit as st
import hashlib
import energy_dashboard
from db_connection import get_database

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------
st.set_page_config(page_title="ECOSAVER", layout="wide")

# Load custom CSS
def load_css(file_path="style/style.css"):
    try:
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ CSS file not found. Please check style/style.css path.")

load_css()

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
db = get_database()
users_collection = db["users"]
energy_collection = db["energy_data"]

# -------------------------------
# SESSION STATE SETUP
# -------------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

# -------------------------------
# LOGOUT FUNCTION
# -------------------------------
def logout():
    st.session_state["user"] = None
    st.rerun()

# -------------------------------
# LOGIN / REGISTER VIEW
# -------------------------------
if not st.session_state["user"]:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(
            "<h1 style='text-align:center; color:#22c55e;'>🔋 ECOSAVER — Smart Energy Login</h1>",
            unsafe_allow_html=True
        )
        tab1, tab2 = st.tabs(["🔑 Login", "🆕 Register"])

        # -------------------------------
        # LOGIN TAB
        # -------------------------------
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                "<h4 style='text-align:center; color:#22c55e;'>Welcome Back 👋</h4>",
                unsafe_allow_html=True
            )

            with st.container():
                login_email = st.text_input("📧 Email", key="login_email", placeholder="Enter your email")
                login_password = st.text_input("🔒 Password", type="password", key="login_password", placeholder="Enter your password")
                login_btn = st.button("Login", use_container_width=True)

            if login_btn:
                if login_email and login_password:
                    hashed_password = hashlib.sha256(login_password.encode()).hexdigest()
                    user = users_collection.find_one({"email": login_email, "password": hashed_password})
                    if user:
                        st.session_state["user"] = user
                        st.success(f"✅ Login successful! Welcome {user['name']} 👋")
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password.")
                else:
                    st.warning("⚠️ Please enter both email and password.")

        # -------------------------------
        # REGISTER TAB
        # -------------------------------
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                "<h4 style='text-align:center; color:#22c55e;'>Create Your Account 🌱</h4>",
                unsafe_allow_html=True
            )

            reg_name = st.text_input("👤 Name", key="reg_name", placeholder="Enter your name")
            reg_email = st.text_input("📧 Email", key="reg_email", placeholder="Enter your email")
            reg_password = st.text_input("🔒 Password", type="password", key="reg_password", placeholder="Create a password")
            appliances = st.multiselect(
                "⚙️ Select Your Appliances",
                ["AC", "Refrigerator", "Washing Machine", "TV"]
            )
            register_btn = st.button("Register", use_container_width=True)

            if register_btn:
                if reg_name and reg_email and reg_password:
                    if users_collection.find_one({"email": reg_email}):
                        st.warning("⚠️ User already exists. Please log in.")
                    else:
                        hashed_password = hashlib.sha256(reg_password.encode()).hexdigest()
                        users_collection.insert_one({
                            "name": reg_name,
                            "email": reg_email,
                            "password": hashed_password,
                            "appliances": appliances
                        })
                        energy_dashboard.simulate_iot_data(reg_email, appliances, energy_collection)
                        st.success("✅ Registration successful! Please log in.")
                else:
                    st.warning("⚠️ Please fill all fields before registering.")

# -------------------------------
# DASHBOARD VIEW
# -------------------------------
else:
    user = st.session_state["user"]

    # Simple top welcome line
    st.markdown(
        f"""
        <div style="background-color:#111827; padding:15px 25px; border-radius:10px;
                    display:flex; justify-content:space-between; align-items:center;">
            <h3 style="color:#22c55e; margin:0;">⚡ ECOSAVER Dashboard</h3>
            <div style="color:white; font-size:16px;">Logged in as: <b>{user['name']}</b> ({user['email']})</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚪 Logout"):
        logout()

    st.divider()
    energy_dashboard.run_dashboard(user["email"])
