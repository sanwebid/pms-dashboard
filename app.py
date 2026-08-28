import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Page Setup
st.set_page_config(page_title="PMS Dashboard Ultra Pro", layout="wide")
st.title("🛡️ PMS Dashboard Ultra Pro")

# Google Sheets se connection aur data caching
# @st.cache_data ki wajah se data bar-bar load nahi hoga, making it ultra-fast!
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Apni Master Sheet ka URL yahan dalein
    df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1OhVynPQC2-ZbeH47bSOG2vPms_R71M3398Fs1kXSfok/edit", worksheet="MasterData")
    return df

with st.spinner("Fetching Master Data..."):
    df = load_data()

# --- FILTERS ---
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    fy_filter = st.selectbox("FY Select", df['FY'].unique())
with col2:
    search_term = st.text_input("Global Search (Txn, Name, Desc)")
with col3:
    cat_filter = st.selectbox("Category", ["All"] + list(df['Category'].dropna().unique()))

# Apply Filters
filtered_df = df[df['FY'] == fy_filter]
if search_term:
    # Search across multiple columns
    filtered_df = filtered_df[filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
if cat_filter != "All":
    filtered_df = filtered_df[filtered_df['Category'] == cat_filter]

# --- PIVOT TABLE (JS code ka Python alternative) ---
st.subheader("📊 Category vs Month Summary")
if not filtered_df.empty:
    pivot_df = pd.pivot_table(
        filtered_df, 
        values='Bank Amount', 
        index='Category', 
        columns='Date', # Aap yahan Month column use kar sakte hain
        aggfunc='sum', 
        fill_value=0
    )
    st.dataframe(pivot_df, use_container_width=True)

# --- DETAILED TRANSACTIONS TABLE ---
st.subheader("📝 Filtered Transactions")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# Export Data Button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Export Data",
    data=csv,
    file_name='PMS_Export.csv',
    mime='text/csv',
)
