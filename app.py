import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Art of Civic Duty", page_icon="🏛️", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #2c3e50;}
    .stDataFrame {font-size: 16px;}
    div[data-testid="stMetricValue"] {font-size: 24px;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
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

# --- KEYWORDS ---
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
def get_council_feed():
    # DIRECT FEED: This is the official RSS feed for Philadelphia City Council
    # It bypasses the messy website entirely.
    rss_url = "https://phila.legistar.com/Feed.aspx?Mode=Calendar&Client=Philadelphia"
    
    try:
        response = requests.get(rss_url, timeout=10)
        # Parse the XML "Radio Signal"
        root = ET.fromstring(response.content)
        
        # Extract the meetings from the feed
        meetings = []
        for item in root.findall('.//item'):
            meeting = {
                "Meeting Name": item.find('title').text if item.find('title') is not None else "Unknown",
                "Date": "Check Link", # RSS sometimes hides the raw date, but title has it
                "Link": item.find('link').text if item.find('link') is not None else "#"
            }
            # Try to clean up the title (Format often: "Committee Name - Date - Time")
            if " - " in meeting["Meeting Name"]:
                parts = meeting["Meeting Name"].split(" - ")
                if len(parts) >= 2:
                    meeting["Meeting Name"] = parts[0]
                    meeting["Date"] = parts[1]
            
            meetings.append(meeting)
            
        if meetings:
            return pd.DataFrame(meetings)
            
    except Exception as e:
        # st.error(f"Feed Error: {e}")
        pass
        
    return pd.DataFrame()

# --- DASHBOARD ---
st.title("🏛️ Philadelphia Governance Dashboard")

if focus_mode == "Society Hill & Old City (Local)":
    st.info(f"🔎 Focused Mode: Showing only updates for **{focus_mode}**.")

tab1, tab2, tab3 = st.tabs(["📜 City Council", "🏗️ Zoning (ZBA)", "🧱 Historic Preservation"])

with tab1:
    df = get_council_feed()
    
    if not df.empty:
        # Apply Filters
        if focus_mode == "Society Hill & Old City (Local)":
            pattern = '|'.join(LOCAL_KEYWORDS)
            # Filter specifically on the Meeting Name or any details we have
            filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
        elif focus_mode == "Center City (Broad)":
            pattern = '|'.join(ALL_KEYWORDS)
            filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
        else:
            filtered_df = df
            
        # Display the Data
        if not filtered_df.empty:
            st.write(f"**Found {len(filtered_df)} upcoming meetings:**")
            st.dataframe(
                filtered_df.style.apply(highlight_rows, axis=1), 
                column_config={"Link": st.column_config.LinkColumn("Meeting Details")},
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.write("No meetings found matching your keywords right now.")
            if not df.empty:
                st.caption("Here are all upcoming meetings:")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
    else:
        st.warning("⚠️ Could not tune into the City Council Feed. (The RSS signal might be offline).")
        st.link_button("Open Legistar Calendar Manually", "https://phila.legistar.com/Calendar.aspx")

with tab2:
    st.header("Zoning Watch")
    c1, c2 = st.columns(2)
    c1.link_button("Check Society Hill Zoning", "https://atlas.phila.gov/")
    c2.link_button("ZBA Calendar", "https://li.phila.gov/zba-appeals-calendar")

with tab3:
    st.header("Historic Preservation")
    st.link_button("Historical Commission Agenda", "https://www.phila.gov/departments/philadelphia-historical-commission/public-meetings/")