import streamlit as st
import pandas as pd
import requests
import urllib3

# Suppress SSL warnings (needed for some gov sites)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Art of Civic Duty", page_icon="🏛️", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #2c3e50;}
    .stDataFrame {font-size: 16px;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: THE WATCHTOWER ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Flag_of_Philadelphia%2C_Pennsylvania.svg/320px-Flag_of_Philadelphia%2C_Pennsylvania.svg.png", width=100)
    st.title("Art of Civic Duty")
    st.caption("Monitoring Philadelphia Governance")
    
    st.header("⚡ Quick Focus")
    focus_mode = st.radio(
        "Select Scope:",
        ["All Activity", "Center City (Broad)", "Society Hill & Old City (Local)"],
        index=0
    )
    
    st.divider()
    st.header("⚙️ Settings")
    ntfy_topic = st.text_input("ntfy.sh Topic", "art_civic_philly")
    if st.button("Test Alert"):
        try:
            requests.post(f"https://ntfy.sh/{ntfy_topic}", data="Test: The Art of Civic Duty is active.".encode('utf-8'))
            st.success("Ping sent!")
        except:
            st.error("Connection failed")

# --- KEYWORD DEFINITIONS ---
LOCAL_KEYWORDS = ["Society Hill", "Old City", "District 1", "Squilla", "Washington Square", "Head House", "Penn's Landing", "Spruce St", "Pine St"]
CENTER_CITY_KEYWORDS = ["Center City", "Market St", "Broad St", "Rittenhouse", "Logan Square", "Chinatown", "City Hall", "Vine St"]
ALL_KEYWORDS = LOCAL_KEYWORDS + CENTER_CITY_KEYWORDS

# --- HELPER FUNCTIONS ---
def highlight_rows(row):
    row_text = str(row.values).lower()
    for k in LOCAL_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
    for k in CENTER_CITY_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #d1ecf1; color: #0c5460'] * len(row)
    return [''] * len(row)

@st.cache_data(ttl=300)
def get_council_agenda():
    url = "https://phila.legistar.com/Calendar.aspx"
    try:
        # STEALTH MODE: Fake ID to look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # verify=False ignores SSL certificate errors (common on old gov sites)
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status() # Check if they blocked us (403 Forbidden)

        df_list = pd.read_html(response.content)
        if df_list:
            df = df_list[0]
            cols = [c for c in df.columns if any(x in c for x in ["Name", "Date", "Time", "Location", "Agenda"])]
            return df[cols]
    except Exception as e:
        # If it fails, print the ACTUAL error so we know why
        st.error(f"⚠️ City Connection Error: {e}") 
        return pd.DataFrame()
    return pd.DataFrame()

# --- MAIN DASHBOARD ---
st.title("🏛️ Philadelphia Governance Dashboard")

if focus_mode == "Society Hill & Old City (Local)":
    st.info(f"🔎 Focused Mode: Showing only updates for **{focus_mode}**.")
elif focus_mode == "Center City (Broad)":
    st.info(f"🔎 Broad Mode: Showing updates for **{focus_mode}**.")

tab1, tab2, tab3 = st.tabs(["📜 City Council", "🏗️ Zoning (ZBA)", "🧱 Historic Preservation"])

with tab1:
    df = get_council_agenda()
    if not df.empty:
        if focus_mode == "Society Hill & Old City (Local)":
            pattern = '|'.join(LOCAL_KEYWORDS)
            df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
        elif focus_mode == "Center City (Broad)":
            pattern = '|'.join(ALL_KEYWORDS)
            df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
            
        st.dataframe(df.style.apply(highlight_rows, axis=1), use_container_width=True, hide_index=True)
        if df.empty: st.write("No agenda items found for this specific focus area right now.")
    else:
        st.warning("Trying to connect to Legistar... (If this persists, the City may be blocking cloud traffic)")

with tab2:
    st.header("Zoning Watch")
    c1, c2 = st.columns(2)
    c1.link_button("Check Society Hill Zoning", "https://atlas.phila.gov/")
    c2.link_button("ZBA Calendar", "https://li.phila.gov/zba-appeals-calendar")

with tab3:
    st.header("Historic Preservation")
    st.link_button("Historical Commission Agenda", "https://www.phila.gov/departments/philadelphia-historical-commission/public-meetings/")