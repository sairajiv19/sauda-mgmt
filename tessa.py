import streamlit as st
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime

# ---------------- Models ----------------
class SaudaModel(BaseModel):
    name: str = Field(..., description="Sauda/deal name")
    broker_id: str = Field(..., description="Associated broker ID")
    party_name: str = Field(..., description="Party or firm name")
    date_of_purchase: datetime = Field(..., description="Date of deal")
    total_lots: int = Field(..., ge=0)
    rate: float = Field(..., gt=0)
    status: str = Field(default="INITIATE_PHASE")

class BrokerModel(BaseModel):
    broker_id: str = Field(..., description="Unique broker ID")
    name: str = Field(..., description="Broker name")

# ---------------- Fake Data ----------------
initial_saudas = [
    SaudaModel(name="Rice Sale A1", broker_id="BRK001", party_name="Sharma Agro", date_of_purchase=datetime(2025,10,1), total_lots=6, rate=4200, status="Pending"),
    SaudaModel(name="Rice Deal B5", broker_id="BRK002", party_name="Gupta Traders", date_of_purchase=datetime(2025,9,30), total_lots=6, rate=4150, status="Completed"),
    SaudaModel(name="Wheat Deal X9", broker_id="BRK001", party_name="Kumar Industries", date_of_purchase=datetime(2025,9,25), total_lots=3, rate=3900, status="Pending"),
]

initial_brokers = [
    BrokerModel(broker_id="BRK001", name="Rajesh Broker"),
    BrokerModel(broker_id="BRK002", name="Agro Link"),
    BrokerModel(broker_id="BRK003", name="Vivek Traders"),
]

# Initialize session data
if "saudas" not in st.session_state:
    st.session_state["saudas"] = initial_saudas
if "brokers" not in st.session_state:
    st.session_state["brokers"] = initial_brokers
if "add_sauda" not in st.session_state:
    st.session_state["add_sauda"] = False
if "add_broker" not in st.session_state:
    st.session_state["add_broker"] = False
if "selected_sauda" not in st.session_state:
    st.session_state["selected_sauda"] = None
if "selected_lots" not in st.session_state:
    st.session_state["selected_lots"] = {}

st.markdown("""
<style>
    /* Remove default padding */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Grey background for main content area */
    .main {
        background-color: #f0f2f6;
    }
    
    /* Make container expand full width */
    .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 2rem;
    }
    

    /* Navbar styling */
    .custom-navbar {
        background: linear-gradient(135deg, #2C3E50 0%, #3498db 100%);
        padding: 1.2rem 2rem;
        margin: 0rem -2rem 2rem -2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    
    .navbar-title {
        color: white;
        font-size: 28px;
        font-weight: 600;
        margin: 0;
        letter-spacing: 0.5px;
    }
    
    .navbar-subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 14px;
        margin-top: 4px;
    }

    
    /* Table styling */
    table {
        width: 100% !important;
        border-collapse: collapse;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Table header styling */
    .table-header-row {
        background-color: #f8f9fa;
        padding: 12px;
        border-bottom: 2px solid #dee2e6;
        font-weight: 600;
        color: #2C3E50;
    }
    
    .table-row {
        background-color: white;
        padding: 12px;
        border-bottom: 1px solid #e0e0e0;
        transition: background-color 0.2s;
    }
    
    .table-row:hover {
        background-color: #f8f9fa;
    }
    
    /* Button styling improvements */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Lot card styling */
    div[data-testid="column"] > div > div > button {
        height: 80px;
        font-size: 16px;
        font-weight: 600;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        color: #2C3E50;
    }
    
    [data-testid="stMetricLabel"] {
        color: #666;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- Custom Styles ----------------
def style_dataframe(df):
    """Apply clean borderless styling to dataframe"""
    return df.style.set_properties(**{
        'background-color': 'white',
        'color': '#333',
        'border': 'none',
        'font-size': '14px',
        'text-align': 'left',
        'padding': '12px'
    }).set_table_styles([
        {'selector': 'thead th', 'props': [
            ('background-color', '#2C3E50'),
            ('color', 'white'),
            ('font-weight', 'bold'),
            ('text-align', 'left'),
            ('border', 'none'),
            ('padding', '14px')
        ]},
        {'selector': 'tbody tr:nth-child(even)', 'props': [
            ('background-color', '#f9f9f9')
        ]},
        {'selector': 'tbody tr:hover', 'props': [
            ('background-color', '#e8f4f8'),
            ('cursor', 'pointer')
        ]},
        {'selector': 'table', 'props': [
            ('border-collapse', 'collapse'),
            ('width', '100%'),
            ('border', 'none')
        ]}
    ]).hide(axis='index')

# ---------------- Layout ----------------
st.set_page_config(page_title="Sauda Management System", layout="wide")

page = st.sidebar.selectbox("Navigate", ["Sauda Deals", "Brokers"], index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Sauda Management System © 2025")

# ---------------- Sauda Page ----------------
if page == "Sauda Deals":
    # Check if viewing a specific sauda
    if st.session_state["selected_sauda"] is not None:
        sauda = st.session_state["saudas"][st.session_state["selected_sauda"]]
        
        # Custom Navbar
        st.markdown(f"""
        <div class="custom-navbar">
            <div>
                <div class="navbar-title">{sauda.name}</div>
                <div class="navbar-subtitle">Sauda Details & Lot Management</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        back_col, _, add_col = st.columns([1, 4, 1])
        with back_col:
            if st.button("← Back to List", use_container_width=True, type="secondary"):
                st.session_state["selected_sauda"] = None
                st.rerun()
        
        # Display sauda details in card
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        with info_col1:
            st.metric("Party Name", sauda.party_name)
        with info_col2:
            st.metric("Broker ID", sauda.broker_id)
        with info_col3:
            st.metric("Rate", f"₹{sauda.rate:,.2f}")
        with info_col4:
            st.metric("Status", sauda.status)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"#### Lot Selection ({sauda.total_lots} lots available)")
        st.caption("Click on lots to select/deselect them")
        
        # Initialize selected lots for this sauda if not exists
        sauda_key = sauda.name
        if sauda_key not in st.session_state["selected_lots"]:
            st.session_state["selected_lots"][sauda_key] = set()
        
        # Display lot cards in grid
        cols_per_row = 6
        for i in range(0, sauda.total_lots, cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                lot_number = i + j + 1
                if lot_number > sauda.total_lots:
                    break
                
                with cols[j]:
                    is_selected = lot_number in st.session_state["selected_lots"][sauda_key]
                    
                    if st.button(
                        f"Lot {lot_number}",
                        key=f"lot_{lot_number}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"
                    ):
                        if is_selected:
                            st.session_state["selected_lots"][sauda_key].remove(lot_number)
                        else:
                            st.session_state["selected_lots"][sauda_key].add(lot_number)
                        st.rerun()
        
        # Show selected lots summary
        if st.session_state["selected_lots"][sauda_key]:
            selected_count = len(st.session_state["selected_lots"][sauda_key])
            st.success(f"**Selected Lots:** {selected_count} / {sauda.total_lots}")
            st.write(f"**Lot Numbers:** {', '.join(map(str, sorted(st.session_state['selected_lots'][sauda_key])))}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Custom Navbar for main list
        st.markdown(f"""
        <div class="custom-navbar">
            <div>
                <div class="navbar-title">Sauda Deals Overview</div>
                <div class="navbar-subtitle">Manage and track all your deals</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add button row
        _, _, _, _, _, add_col = st.columns([1, 1, 1, 1, 1, 1])
        with add_col:
            button_label = "➖ Close Form" if st.session_state["add_sauda"] else "➕ Add New Deal"
            if st.button(button_label, type="primary", key="sauda_toggle", use_container_width=True):
                st.session_state["add_sauda"] = not st.session_state["add_sauda"]
                st.rerun()

        # Inline Add Section
        if st.session_state["add_sauda"]:
            with st.form("add_sauda_form"):
                st.markdown("#### Add New Sauda")
                col1, col2 = st.columns(2)
                name = col1.text_input("Deal Name")
                broker_id = col2.text_input("Broker ID")
                party_name = col1.text_input("Party Name")
                date_of_purchase = col2.date_input("Date of Purchase", datetime.now())
                total_lots = col1.number_input("Total Lots", min_value=0)
                rate = col2.number_input("Rate ₹", min_value=0.0)
                status = st.selectbox("Status", ["INITIATE_PHASE", "Pending", "Completed", "Cancelled"])

                submitted = st.form_submit_button("✓ Submit Deal", use_container_width=True, type="primary")
                if submitted:
                    try:
                        new_sauda = SaudaModel(
                            name=name,
                            broker_id=broker_id,
                            party_name=party_name,
                            date_of_purchase=datetime.combine(date_of_purchase, datetime.min.time()),
                            total_lots=total_lots,
                            rate=rate,
                            status=status,
                        )
                        st.session_state["saudas"].append(new_sauda)
                        st.success(f"✓ Sauda '{name}' added successfully!")
                        st.session_state["add_sauda"] = False
                        st.rerun()
                    except ValidationError as e:
                        st.error(str(e))
            st.markdown('</div>', unsafe_allow_html=True)

        # Display table with headers
        st.caption("Click 'View' to manage lots for each deal")
        
        # Table header
        header_cols = st.columns([2, 1.5, 1.5, 1.5, 1, 1])
        with header_cols[0]:
            st.markdown("**Name**")
        with header_cols[1]:
            st.markdown("**Broker ID**")
        with header_cols[2]:
            st.markdown("**Party Name**")
        with header_cols[3]:
            st.markdown("**Date**")
        with header_cols[4]:
            st.markdown("**Total Lots**")
        with header_cols[5]:
            st.markdown("**Action**")
        
        st.divider()
        
        # Table rows
        for idx, sauda in enumerate(st.session_state["saudas"]):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1.5, 1, 1])
            with col1:
                st.write(sauda.name)
            with col2:
                st.write(sauda.broker_id)
            with col3:
                st.write(sauda.party_name)
            with col4:
                st.write(sauda.date_of_purchase.strftime('%Y-%m-%d'))
            with col5:
                st.write(sauda.total_lots)
            with col6:
                if st.button("View →", key=f"view_{idx}", use_container_width=True):
                    st.session_state["selected_sauda"] = idx
                    st.rerun()
            
            if idx < len(st.session_state["saudas"]) - 1:
                st.divider()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Broker Page ----------------
if page == "Brokers":
    # Custom Navbar for brokers
    st.markdown(f"""
    <div class="custom-navbar">
        <div>
            <div class="navbar-title">Brokers Management</div>
            <div class="navbar-subtitle">Manage broker information and contacts</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add button row
    _, _, _, _, _, add_col = st.columns([1, 1, 1, 1, 1, 1])
    with add_col:
        button_label = "➖ Close Form" if st.session_state["add_broker"] else "➕ Add New Broker"
        if st.button(button_label, type="primary", key="broker_toggle", use_container_width=True):
            st.session_state["add_broker"] = not st.session_state["add_broker"]
            st.rerun()

    if st.session_state["add_broker"]:
        with st.form("add_broker_form"):
            st.markdown("#### Add New Broker")
            col1, col2 = st.columns(2)
            broker_id = col1.text_input("Broker ID")
            name = col2.text_input("Broker Name")
            submitted = st.form_submit_button("✓ Submit Broker", use_container_width=True, type="primary")
            if submitted:
                try:
                    new_broker = BrokerModel(broker_id=broker_id, name=name)
                    st.session_state["brokers"].append(new_broker)
                    st.success(f"✓ Broker '{name}' added successfully!")
                    st.session_state["add_broker"] = False
                    st.rerun()
                except ValidationError as e:
                    st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

    df_b = pd.DataFrame([b.model_dump() for b in st.session_state["brokers"]])
    st.write(style_dataframe(df_b).to_html(), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
