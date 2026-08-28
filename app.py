import streamlit as st
import pandas as pd

# Page Setup
st.set_page_config(page_title="PMS Dashboard Ultra Pro", layout="wide")
st.title("🛡️ PMS Dashboard Ultra Pro")

# Direct Data Loading Method
@st.cache_data(ttl=600)
def load_data():
    sheet_id = "1OhVynPQC2-ZbeH47bSOG2vPms_R71M3398Fs1kXSfok"
    sheet_name = "MasterData" 
    
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    
    # 1. Amount Cleaning
    if 'Bank Amount' in df.columns:
        df['Bank Amount'] = df['Bank Amount'].astype(str).str.replace(r'[^\d.-]', '', regex=True)
        df['Bank Amount'] = pd.to_numeric(df['Bank Amount'], errors='coerce').fillna(0.0)
        
    # 2. Category Blank Handling (Making it UPPERCASE strictly for matching)
    if 'Category' in df.columns:
        df['Category'] = df['Category'].fillna('BLANK').replace(r'^\s*$', 'BLANK', regex=True).str.upper()

    # 3. DATE FIX: Text Date to real Date objects
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
        
    return df

with st.spinner("Fetching Master Data..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Data load hone me problem aayi. Error: {e}")
        st.stop()

# --- CREATE TABS ---
tab1, tab2 = st.tabs(["📊 Tab 1: Category vs Month Summary (Pivot)", "📝 Tab 2: Detailed Transactions (All Data)"])

# ==========================================
# TAB 1: PIVOT TABLE & DRILL DOWN
# ==========================================
with tab1:
    st.markdown("### 📌 Summary Dashboard")
    
    # Only FY Filter for Pivot
    fy_list = df['FY'].dropna().unique() if 'FY' in df.columns else []
    fy_filter = st.selectbox("Select Financial Year (Affects only Pivot)", fy_list, key="fy_pivot")
    
    pivot_source_df = df.copy()
    if 'FY' in pivot_source_df.columns:
        pivot_source_df = pivot_source_df[pivot_source_df['FY'] == fy_filter]

    if not pivot_source_df.empty and 'Category' in df.columns and 'Source' in df.columns and 'Bank Amount' in df.columns:
        # DUPLICATE TXN FIX
        if 'Txn No.' in pivot_source_df.columns:
            unique_pivot_data = pivot_source_df.drop_duplicates(subset=['Txn No.'])
        else:
            unique_pivot_data = pivot_source_df

        # Creating Pivot
        pivot_df = pd.pivot_table(
            unique_pivot_data, 
            values='Bank Amount', 
            index='Category', 
            columns='Source', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Month Sequencing
        month_mapping = {"apr": 1, "may": 2, "jun": 3, "jul": 4, "aug": 5, "sep": 6, "oct": 7, "nov": 8, "dec": 9, "jan": 10, "feb": 11, "mar": 12}
        def sort_fy_months(col_name):
            col_str = str(col_name).strip().lower()
            for month_name, order in month_mapping.items():
                if col_str.startswith(month_name): return order
            return 99
            
        sorted_columns = sorted(pivot_df.columns, key=sort_fy_months)
        pivot_df = pivot_df[sorted_columns]
        
        # Grand Total Column
        pivot_df['Grand Total'] = pivot_df.sum(axis=1)

        # CUSTOM CATEGORY SORTING (Aapki Requirement Ke Hisaab Se)
        custom_order = ['LL', 'MOBILE', 'RENT', 'SCRAP', 'CTOPUP', 'SIM', 'LC', 'OTHER', 'SCHOOL', 'BLANK']
        
        # Filter only those categories that actually exist in the current pivot data
        existing_order = [cat for cat in custom_order if cat in pivot_df.index]
        missing_cats = [cat for cat in pivot_df.index if cat not in custom_order]
        final_index = existing_order + missing_cats # Nayi category aaye toh wo 'Blank' ke baad aaye
        
        pivot_df = pivot_df.reindex(final_index)
        
        # GRAND TOTAL ROW (Neeche Total Row Add Karna)
        pivot_df.loc['TOTAL'] = pivot_df.sum(axis=0)

        # Display Pivot Table
        st.dataframe(pivot_df, use_container_width=True)
        
        st.divider()
        
        # --- DRILL DOWN FEATURE (Option B) ---
        st.markdown("#### 🔍 Click & View Data (Drill-Down)")
        col_drill_1, col_drill_2 = st.columns(2)
        with col_drill_1:
            drill_cat = st.selectbox("Select Category to View Details", ["-- Select Category --"] + list(pivot_df.index[:-1])) # Exclude 'TOTAL' from dropdown
        with col_drill_2:
            drill_source = st.selectbox("Select Month (Source) to View Details", ["-- Select Month --"] + list(pivot_df.columns[:-1])) # Exclude 'Grand Total' from dropdown
            
        if drill_cat != "-- Select Category --" and drill_source != "-- Select Month --":
            drill_data = unique_pivot_data[(unique_pivot_data['Category'] == drill_cat) & (unique_pivot_data['Source'] == drill_source)]
            st.success(f"Showing Data for: {drill_cat} in {drill_source} ({len(drill_data)} records)")
            st.dataframe(drill_data, use_container_width=True, hide_index=True, column_config={"Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY")})

# ==========================================
# TAB 2: DETAILED DATA & ADVANCED FILTERS
# ==========================================
with tab2:
    st.markdown("### 🔎 Advanced Data Filtering")
    detailed_df = df.copy()
    
    # Filter Row 1
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        date_range = st.date_input("Date Range (Start - End)", value=[], key="date_filter")
    with f_col2:
        desc_search = st.text_input("🔍 Search Description", key="desc_filter")
    with f_col3:
        phone_search = st.text_input("📞 Search Phone Number", key="phone_filter")
        
    # Filter Row 2
    f_col4, f_col5, f_col6 = st.columns(3)
    with f_col4:
        cat_list = list(detailed_df['Category'].dropna().unique()) if 'Category' in detailed_df.columns else []
        cat_filter = st.multiselect("Select Categories", cat_list, key="cat_filter")
    with f_col5:
        source_list = list(detailed_df['Source'].dropna().unique()) if 'Source' in detailed_df.columns else []
        source_filter = st.multiselect("Select Source (Month)", source_list, key="source_filter")
    with f_col6:
        # Amount Search Type (Exact or Range)
        amt_type = st.radio("Amount Filter Type", ["Show All", "Exact Amount", "Custom Range"], horizontal=True)

    # Filter Row 3 (Conditionally shown based on Amount Filter Type)
    if amt_type == "Exact Amount":
        exact_amt = st.number_input("Enter Exact Bank Amount", min_value=0.0, step=100.0)
    elif amt_type == "Custom Range":
        r_col1, r_col2 = st.columns(2)
        min_amt = r_col1.number_input("Min Amount", value=0.0)
        max_amt = r_col2.number_input("Max Amount", value=1000000.0)

    # --- APPLY TAB 2 FILTERS ---
    # 1. Date Range Filter
    if len(date_range) == 2:
        detailed_df = detailed_df[(detailed_df['Date'] >= date_range[0]) & (detailed_df['Date'] <= date_range[1])]
    
    # 2. Description Search
    if desc_search:
        detailed_df = detailed_df[detailed_df['Description'].astype(str).str.contains(desc_search, case=False)]
        
    # 3. Phone Search
    if phone_search:
        detailed_df = detailed_df[detailed_df['Phone'].astype(str).str.contains(phone_search, case=False)]
        
    # 4. Category Filter
    if cat_filter:
        detailed_df = detailed_df[detailed_df['Category'].isin(cat_filter)]
        
    # 5. Source Filter
    if source_filter:
        detailed_df = detailed_df[detailed_df['Source'].isin(source_filter)]
        
    # 6. Amount Filter
    if amt_type == "Exact Amount" and exact_amt > 0:
        detailed_df = detailed_df[detailed_df['Bank Amount'] == exact_amt]
    elif amt_type == "Custom Range":
        detailed_df = detailed_df[(detailed_df['Bank Amount'] >= min_amt) & (detailed_df['Bank Amount'] <= max_amt)]

    st.divider()
    
    st.write(f"**Total Records Found: {len(detailed_df)}**")
    st.dataframe(
        detailed_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={"Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY")}
    )

    # Export Data Button
    csv = detailed_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Filtered Data",
        data=csv,
        file_name='PMS_Filtered_Export.csv',
        mime='text/csv',
    )
