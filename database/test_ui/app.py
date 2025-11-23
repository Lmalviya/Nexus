import streamlit as st
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
# Assuming .env is in ../postgress/.env relative to this file
load_dotenv(os.path.join(os.path.dirname(__file__), '../postgress/.env'))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nexus_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

st.set_page_config(page_title="Nexus DB Tester", layout="wide")
st.title("Nexus Database Testing UI")

menu = ["Organizations", "Users", "User Settings"]
choice = st.sidebar.selectbox("Select Table", menu)

if choice == "Organizations":
    st.header("Organizations")
    
    # View
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM organizations", conn)
        st.dataframe(df)
        conn.close()
    except Exception as e:
        st.error(f"Error connecting to DB: {e}")

    # Add
    st.subheader("Add Organization")
    with st.form("add_org_form"):
        name = st.text_input("Name")
        slug = st.text_input("Slug")
        domain = st.text_input("Domain")
        plan_tier = st.selectbox("Plan Tier", ["free", "standard", "pro", "enterprise"])
        max_users = st.number_input("Max Users", min_value=1, value=10)
        submitted = st.form_submit_button("Add Organization")
        
        if submitted:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO organizations (name, slug, domain, plan_tier, max_users) VALUES (%s, %s, %s, %s, %s)",
                    (name, slug, domain, plan_tier, max_users)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success("Organization added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding organization: {e}")

elif choice == "Users":
    st.header("Users")
    
    # View
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM users", conn)
        st.dataframe(df)
        
        # Get orgs for dropdown
        orgs_df = pd.read_sql("SELECT id, name FROM organizations", conn)
        org_options = {row['name']: row['id'] for index, row in orgs_df.iterrows()}
        
        conn.close()
    except Exception as e:
        st.error(f"Error connecting to DB: {e}")
        org_options = {}

    # Add
    st.subheader("Add User")
    with st.form("add_user_form"):
        if org_options:
            org_name = st.selectbox("Organization", list(org_options.keys()))
            org_id = org_options[org_name]
        else:
            st.warning("No organizations found. Create one first.")
            org_id = None
            
        email = st.text_input("Email")
        full_name = st.text_input("Full Name")
        role = st.selectbox("Role", ["admin", "employee", "viewer"])
        
        submitted = st.form_submit_button("Add User")
        
        if submitted and org_id:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (organization_id, email, full_name, role) VALUES (%s, %s, %s, %s)",
                    (org_id, email, full_name, role)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success("User added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding user: {e}")

elif choice == "User Settings":
    st.header("User Settings")
    
    # View
    try:
        conn = get_connection()
        query = """
        SELECT us.user_id, u.email, us.preferences, us.updated_at 
        FROM user_settings us
        JOIN users u ON us.user_id = u.id
        """
        df = pd.read_sql(query, conn)
        st.dataframe(df)
        
        # Get users for dropdown
        users_df = pd.read_sql("SELECT id, email FROM users", conn)
        user_options = {row['email']: row['id'] for index, row in users_df.iterrows()}
        
        conn.close()
    except Exception as e:
        st.error(f"Error connecting to DB: {e}")
        user_options = {}

    # Add/Update
    st.subheader("Update User Settings")
    with st.form("update_settings_form"):
        if user_options:
            user_email = st.selectbox("User", list(user_options.keys()))
            user_id = user_options[user_email]
        else:
            st.warning("No users found. Create one first.")
            user_id = None
            
        theme = st.selectbox("Theme", ["system", "light", "dark"])
        language = st.text_input("Language", value="en-IN")
        
        submitted = st.form_submit_button("Save Settings")
        
        if submitted and user_id:
            try:
                conn = get_connection()
                cur = conn.cursor()
                preferences = f'{{"theme": "{theme}", "language": "{language}"}}'
                
                # Upsert
                cur.execute(
                    """
                    INSERT INTO user_settings (user_id, preferences) 
                    VALUES (%s, %s::jsonb)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET preferences = user_settings.preferences || EXCLUDED.preferences, updated_at = NOW()
                    """,
                    (user_id, preferences)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success("Settings saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving settings: {e}")
