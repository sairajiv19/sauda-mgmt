import streamlit as st
import pandas as pd
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from datetime import datetime, UTC
from typing import Optional
from bson import ObjectId


# ---------------- Models ----------------
class FRKBhejaModel(BaseModel):
    """FRK Bheja nested model"""
    via: str = Field(..., description="Transport method")
    qty: float = Field(..., gt=0, description="Quantity sent")


class LotModel(BaseModel):
    """Lot Collection Model"""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    sauda_id: ObjectId = Field(..., description="Reference to parent sauda")
    rice_lot_no: Optional[str] = Field(None, description="Rice lot number")

    # FRK and Gate Pass
    frk: bool = Field(default=False, description="FRK status")
    frk_bheja: Optional[FRKBhejaModel] = Field(None, description="FRK shipment details")
    frk_bheja_date: Optional[datetime] = Field(None, description="FRK shipment date")
    gate_pass_date: Optional[datetime] = Field(None, description="Gate pass issue date")
    gate_pass_via: Optional[str] = Field(None, description="Gate pass location")

    # Purchase + Cost merged fields
    rice_pass_date: Optional[datetime] = Field(None, description="Rice pass date")
    rice_deposit_centre: Optional[str] = Field(None, description="Storage/deposit location")
    qtl: float = Field(..., gt=0, description="Quantity in quintals")
    rice_bags_quantity: int = Field(..., ge=0, description="Number of bags")
    net_rice_bought: float = Field(..., gt=0, description="Net rice quantity bought")
    moisture_cut: float = Field(default=0, ge=0, description="Moisture cut amount")
    qi_expense: float = Field(default=0, ge=0, description="QI expense")
    lot_dalali_expense: float = Field(default=0, ge=0, description="Dalali/commission expense")
    other_costs: float = Field(default=0, ge=0, description="Other miscellaneous costs")
    brokerage: float = Field(default=0, ge=0, description="Brokerage fees")
    nett_amount: Optional[float] = Field(None, description="Computed total amount")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class SaudaModel(BaseModel):
    """Sauda (Deal) Collection Model"""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    name: str = Field(..., description="Sauda/deal name")
    broker_id: str = Field(..., description="The id of the broker in the system.")
    party_name: str = Field(..., description="Party or firm name")
    purchase_date: datetime = Field(..., description="Sauda date")
    total_lots: int = Field(..., ge=0, description="Total number of lots")
    rate: float = Field(..., gt=0, description="Rate per bora/product")
    rice_type: Optional[str] = Field(None, description="Type of rice")
    rice_agreement: Optional[str] = Field(None, description="Agreement number")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    end_at: Optional[datetime] = Field(None, description="Final date when sauda is complete.")
    status: str = Field(default="INITIATE_PHASE", description="Status of the sauda.")
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class BrokerModel(BaseModel):
    broker_id: str = Field(..., description="Unique broker ID")
    name: str = Field(..., description="Broker name")


# ---------------- Fake Data ----------------
initial_saudas = [
    SaudaModel(
        name="Rice Sale A1",
        broker_id="BRK001",
        party_name="Sharma Agro",
        purchase_date=datetime(2025, 10, 1),
        total_lots=3,
        rate=4200,
        rice_type="Basmati",
        rice_agreement="AGR-2025-001",
        status="Pending",
    ),
    SaudaModel(
        name="Rice Deal B5",
        broker_id="BRK002",
        party_name="Gupta Traders",
        purchase_date=datetime(2025, 9, 30),
        total_lots=2,
        rate=4150,
        rice_type="Sona Masoori",
        rice_agreement="AGR-2025-002",
        status="Completed",
    ),
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
if "selected_lot" not in st.session_state:
    st.session_state["selected_lot"] = None
if "lot_data" not in st.session_state:
    st.session_state["lot_data"] = {}
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False
if "show_confirmation" not in st.session_state:
    st.session_state["show_confirmation"] = False
if "pending_changes" not in st.session_state:
    st.session_state["pending_changes"] = {}


# ---------------- Custom CSS ----------------
st.markdown(
    """
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
    
    /* Content card */
    .content-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    
    /* Lot detail styling */
    .lot-detail-row {
        padding: 12px 0;
        border-bottom: 1px solid #e9ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .lot-detail-label {
        font-weight: 600;
        color: #495057;
        width: 40%;
    }
    
    .lot-detail-value {
        color: #212529;
        width: 60%;
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
""",
    unsafe_allow_html=True,
)


# ---------------- Helper Functions ----------------
def get_or_create_lot(sauda_name, lot_number):
    """Get or create lot data for a specific sauda and lot number"""
    key = f"{sauda_name}_lot_{lot_number}"
    if key not in st.session_state["lot_data"]:
        # Create default lot data
        st.session_state["lot_data"][key] = LotModel(
            sauda_id=ObjectId(),
            rice_lot_no=f"LOT-{lot_number}",
            qtl=100.0,
            rice_bags_quantity=50,
            net_rice_bought=100.0,
        )
    return st.session_state["lot_data"][key]


def style_dataframe(df):
    """Apply clean borderless styling to dataframe"""
    return (
        df.style.set_properties(
            **{
                "background-color": "white",
                "color": "#333",
                "border": "none",
                "font-size": "14px",
                "text-align": "left",
                "padding": "12px",
            }
        )
        .set_table_styles(
            [
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", "#2C3E50"),
                        ("color", "white"),
                        ("font-weight", "bold"),
                        ("text-align", "left"),
                        ("border", "none"),
                        ("padding", "14px"),
                    ],
                },
                {
                    "selector": "tbody tr:nth-child(even)",
                    "props": [("background-color", "#f9f9f9")],
                },
                {
                    "selector": "tbody tr:hover",
                    "props": [("background-color", "#e8f4f8"), ("cursor", "pointer")],
                },
                {
                    "selector": "table",
                    "props": [
                        ("border-collapse", "collapse"),
                        ("width", "100%"),
                        ("border", "none"),
                    ],
                },
            ]
        )
        .hide(axis="index")
    )


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
        st.markdown(
            f"""
        <div class="custom-navbar">
            <div>
                <div class="navbar-title">{sauda.name}</div>
                <div class="navbar-subtitle">Sauda Details & Lot Management</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        back_col, _, _ = st.columns([1, 4, 1])
        with back_col:
            if st.button("← Back to Saudas", use_container_width=True, type="secondary"):
                st.session_state["selected_sauda"] = None
                st.session_state["selected_lot"] = None
                st.session_state["edit_mode"] = False
                st.rerun()

        # Display sauda details in card
        st.markdown("#### Sauda Information")
        info_col1, info_col2, info_col3, info_col4, info_col5, info_col6 = st.columns(6)
        with info_col1:
            st.metric("Party Name", sauda.party_name)
        with info_col2:
            st.metric("Broker ID", sauda.broker_id)
        with info_col3:
            st.metric("Rate", f"₹{sauda.rate:,.2f}")
        with info_col4:
            st.metric("Status", sauda.status)
        with info_col5:
            st.metric("Rice Type", sauda.rice_type or "N/A")
        with info_col6:
            st.metric("Agreement", sauda.rice_agreement or "N/A")
        st.markdown("</div>", unsafe_allow_html=True)

        # Check if a lot is selected
        if st.session_state["selected_lot"] is not None:
            lot_number = st.session_state["selected_lot"]
            lot_key = f"{sauda.name}_lot_{lot_number}"
            lot_data = get_or_create_lot(sauda.name, lot_number)

            # Back to lots button
            back_col, _, edit_col = st.columns([1, 4, 1])
            with back_col:
                if st.button(
                    "← Back to Lots", use_container_width=True, type="secondary"
                ):
                    st.session_state["selected_lot"] = None
                    st.session_state["edit_mode"] = False
                    st.session_state["pending_changes"] = {}
                    st.session_state["show_confirmation"] = False
                    st.rerun()
            with edit_col:
                if not st.session_state["edit_mode"]:
                    if st.button("✏️ Edit", use_container_width=True, type="primary"):
                        st.session_state["edit_mode"] = True
                        st.rerun()
                else:
                    if st.button(
                        "❌ Cancel", use_container_width=True, type="secondary"
                    ):
                        st.session_state["edit_mode"] = False
                        st.session_state["pending_changes"] = {}
                        st.session_state["show_confirmation"] = False
                        st.rerun()

            st.markdown(f"<h2 style='text-align: center;'>Lot → {lot_data.rice_lot_no or f'Lot {lot_number}'}</h2>", unsafe_allow_html=True)
            # st.markdown("<h4 style='text-align: center;'>Lot Information</h4>", unsafe_allow_html=True)

            # Edit button
            edit_col1, edit_col2 = st.columns([5, 1])

            if st.session_state["edit_mode"]:
                # Editable fields without form
                st.markdown("#### Edit Lot Details")

                col1, col2 = st.columns(2)

                rice_lot_no = col1.text_input(
                    "Rice Lot No", value=lot_data.rice_lot_no or "", key="edit_rice_lot_no"
                )

                st.markdown("---")
                st.markdown("**FRK & Gate Pass**")

                frk = st.checkbox("FRK", value=lot_data.frk, key="edit_frk")

                frk_via = ""
                frk_qty = 0.0
                frk_bheja_date = None
                
                if frk:
                    frk_col1, frk_col2 = st.columns(2)
                    frk_via = frk_col1.text_input(
                        "FRK Via",
                        value=lot_data.frk_bheja.via if lot_data.frk_bheja else "",
                        key="edit_frk_via"
                    )
                    frk_qty = frk_col2.number_input(
                        "FRK Qty",
                        value=(
                            float(lot_data.frk_bheja.qty)
                            if lot_data.frk_bheja
                            else 0.0
                        ),
                        min_value=0.0,
                        key="edit_frk_qty"
                    )
                    frk_bheja_date = frk_col1.date_input(
                        "FRK Date",
                        value=(
                            lot_data.frk_bheja_date.date()
                            if lot_data.frk_bheja_date
                            else None
                        ),
                        key="edit_frk_date",
                        format="DD/MM/YYYY"
                    )

                gate_col1, gate_col2 = st.columns(2)
                gate_pass_date = gate_col1.date_input(
                    "Gate Pass Date",
                    value=(
                        lot_data.gate_pass_date.date()
                        if lot_data.gate_pass_date
                        else None
                    ),
                    key="edit_gate_date",
                    format="DD/MM/YYYY"
                )
                gate_pass_via = gate_col2.text_input(
                    "Gate Pass Via", value=lot_data.gate_pass_via or "", key="edit_gate_via"
                )

                st.markdown("---")
                st.markdown("**Purchase Details**")

                purchase_col1, purchase_col2 = st.columns(2)
                rice_pass_date = purchase_col1.date_input(
                    "Rice Pass Date",
                    value=(
                        lot_data.rice_pass_date.date()
                        if lot_data.rice_pass_date
                        else None
                    ),
                    key="edit_rice_pass_date",
                    format="DD/MM/YYYY"
                )
                rice_deposit_centre = purchase_col2.text_input(
                    "Rice Deposit Centre", value=lot_data.rice_deposit_centre or "", key="edit_deposit"
                )
                qtl = purchase_col1.number_input(
                    "Quantity (Qtl)", value=float(lot_data.qtl), min_value=0.0, key="edit_qtl"
                )
                rice_bags_quantity = purchase_col2.number_input(
                    "Rice Bags Quantity",
                    value=int(lot_data.rice_bags_quantity),
                    min_value=0,
                    key="edit_bags"
                )
                net_rice_bought = purchase_col1.number_input(
                    "Net Rice Bought",
                    value=float(lot_data.net_rice_bought),
                    min_value=0.0,
                    key="edit_net_rice"
                )

                st.markdown("---")
                st.markdown("**Cost Details**")

                cost_col1, cost_col2 = st.columns(2)
                moisture_cut = cost_col1.number_input(
                    "Moisture Cut",
                    value=float(lot_data.moisture_cut),
                    min_value=0.0,
                    key="edit_moisture"
                )
                qi_expense = cost_col2.number_input(
                    "QI Expense", value=float(lot_data.qi_expense), min_value=0.0, key="edit_qi"
                )
                lot_dalali_expense = cost_col1.number_input(
                    "Dalali Expense",
                    value=float(lot_data.lot_dalali_expense),
                    min_value=0.0,
                    key="edit_dalali"
                )
                other_costs = cost_col2.number_input(
                    "Other Costs", value=float(lot_data.other_costs), min_value=0.0, key="edit_other"
                )
                brokerage = cost_col1.number_input(
                    "Brokerage", value=float(lot_data.brokerage), min_value=0.0, key="edit_brokerage"
                )
                nett_amount = cost_col2.number_input(
                    "Nett Amount",
                    value=(
                        float(lot_data.nett_amount) if lot_data.nett_amount else 0.0
                    ),
                    min_value=0.0,
                    key="edit_nett"
                )

                st.markdown("---")
                
                if st.button("💾 Save Changes", use_container_width=True, type="primary", key="save_btn"):
                    # Store pending changes
                    st.session_state["pending_changes"] = {
                        "rice_lot_no": rice_lot_no,
                        "frk": frk,
                        "frk_bheja": (
                            FRKBhejaModel(via=frk_via, qty=frk_qty) if frk else None
                        ),
                        "frk_bheja_date": (
                            datetime.combine(frk_bheja_date, datetime.min.time())
                            if frk and frk_bheja_date
                            else None
                        ),
                        "gate_pass_date": (
                            datetime.combine(gate_pass_date, datetime.min.time())
                            if gate_pass_date
                            else None
                        ),
                        "gate_pass_via": gate_pass_via,
                        "rice_pass_date": (
                            datetime.combine(rice_pass_date, datetime.min.time())
                            if rice_pass_date
                            else None
                        ),
                        "rice_deposit_centre": rice_deposit_centre,
                        "qtl": qtl,
                        "rice_bags_quantity": rice_bags_quantity,
                        "net_rice_bought": net_rice_bought,
                        "moisture_cut": moisture_cut,
                        "qi_expense": qi_expense,
                        "lot_dalali_expense": lot_dalali_expense,
                        "other_costs": other_costs,
                        "brokerage": brokerage,
                        "nett_amount": nett_amount,
                    }
                    st.session_state["show_confirmation"] = True
                    st.rerun()

            else:
                # Display mode
                st.markdown("#### FRK & Gate Pass")
                st.markdown(f"**FRK Status:** {'FRK' if lot_data.frk else 'Non FRK'}")

                if lot_data.frk and lot_data.frk_bheja:
                    st.markdown(f"**FRK Via:** {lot_data.frk_bheja.via}")
                    st.markdown(f"**FRK Qty:** {lot_data.frk_bheja.qty}")
                    st.markdown(
                        f"**FRK Bheja Date:** {lot_data.frk_bheja_date.strftime('%d-%m-%Y') if lot_data.frk_bheja_date else 'N/A'}"
                    )

                st.markdown(
                    f"**Gate Pass Date:** {lot_data.gate_pass_date.strftime('%d-%m-%Y') if lot_data.gate_pass_date else 'N/A'}"
                )
                st.markdown(f"**Gate Pass Via:** {lot_data.gate_pass_via or 'N/A'}")

                st.markdown("---")
                st.markdown("#### Purchase Details")
                st.markdown(
                    f"**Rice Pass Date:** {lot_data.rice_pass_date.strftime('%d-%m-%Y') if lot_data.rice_pass_date else 'N/A'}"
                )
                st.markdown(
                    f"**Rice Deposit Centre:** {lot_data.rice_deposit_centre or 'N/A'}"
                )
                st.markdown(f"**Quantity (Qtl):** {lot_data.qtl}")
                st.markdown(f"**Rice Bags Quantity:** {lot_data.rice_bags_quantity}")
                st.markdown(f"**Net Rice Bought:** {lot_data.net_rice_bought}")

                st.markdown("---")
                st.markdown("#### Cost Details")
                st.markdown(f"**Moisture Cut:** ₹{lot_data.moisture_cut:,.2f}")
                st.markdown(f"**QI Expense:** ₹{lot_data.qi_expense:,.2f}")
                st.markdown(f"**Dalali Expense:** ₹{lot_data.lot_dalali_expense:,.2f}")
                st.markdown(f"**Other Costs:** ₹{lot_data.other_costs:,.2f}")
                st.markdown(f"**Brokerage:** ₹{lot_data.brokerage:,.2f}")
                st.markdown(
                    f"**Nett Amount:** ₹{lot_data.nett_amount:,.2f}"
                    if lot_data.nett_amount
                    else "**Nett Amount:** N/A"
                )

                st.markdown("---")
                st.caption(
                    f"Created: {lot_data.created_at.strftime('%d-%m-%Y %H:%M')} | Updated: {lot_data.updated_at.strftime('%d-%m-%Y %H:%M')}"
                )

            # Confirmation dialog at bottom
            if st.session_state["show_confirmation"]:
                st.markdown("---")
                st.warning("⚠️ Are you sure you want to save these changes?")
                conf_col1, conf_col2 = st.columns(2)
                with conf_col1:
                    if st.button(
                        "✓ Yes, Save Changes",
                        use_container_width=True,
                        type="primary",
                        key="confirm_yes",
                    ):
                        # Apply changes
                        for field, value in st.session_state["pending_changes"].items():
                            setattr(lot_data, field, value)
                        lot_data.updated_at = datetime.now(UTC)
                        st.session_state["lot_data"][lot_key] = lot_data
                        st.session_state["show_confirmation"] = False
                        st.session_state["edit_mode"] = False
                        st.session_state["pending_changes"] = {}
                        st.success("✓ Changes saved successfully!")
                        st.rerun()
                with conf_col2:
                    if st.button(
                        "✗ No, Cancel",
                        use_container_width=True,
                        type="secondary",
                        key="confirm_no",
                    ):
                        st.session_state["show_confirmation"] = False
                        st.session_state["pending_changes"] = {}
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        else:
            # Show lot selection
            st.markdown(f"#### Lot Selection ({sauda.total_lots} lots available)")
            st.caption("Click on a lot to view details")

            # Display lot cards in grid
            cols_per_row = 6
            for i in range(0, sauda.total_lots, cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    lot_number = i + j + 1
                    if lot_number > sauda.total_lots:
                        break

                    with cols[j]:
                        lot_key = f"{sauda.name}_lot_{lot_number}"
                        # Get lot data if exists to show rice_lot_no
                        if lot_key in st.session_state["lot_data"]:
                            lot_display = (
                                st.session_state["lot_data"][lot_key].rice_lot_no
                                or f"Lot {lot_number}"
                            )
                        else:
                            lot_display = f"Lot {lot_number}"

                        if st.button(
                            lot_display,
                            key=f"lot_{lot_number}",
                            use_container_width=True,
                            type="primary",
                        ):
                            st.session_state["selected_lot"] = lot_number
                            st.rerun()

    else:
        # Custom Navbar for main list
        st.markdown(
            f"""
        <div class="custom-navbar">
            <div>
                <div class="navbar-title">Sauda Management Overview</div>
                <div class="navbar-subtitle">Manage and track all your saudas</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add button row
        _, _, _, _, _, add_col = st.columns([1, 1, 1, 1, 1, 1])
        with add_col:
            button_label = (
                "➖ Close Form" if st.session_state["add_sauda"] else "➕ Add New Deal"
            )
            if st.button(
                button_label,
                type="primary",
                key="sauda_toggle",
                use_container_width=True,
            ):
                st.session_state["add_sauda"] = not st.session_state["add_sauda"]
                st.rerun()

        # Inline Add Section
        if st.session_state["add_sauda"]:
            with st.form("add_sauda_form"):
                st.markdown("#### Add New Sauda")
                col1, col2 = st.columns(2)
                name = col1.text_input("Deal Name")
                broker_options = [broker.broker_id for broker in st.session_state["brokers"]]
                broker_id = col2.selectbox("Broker ID", options=broker_options)
                party_name = col1.text_input("Party Name")
                purchase_date = col2.date_input("Purchase Date", datetime.now(), format="DD/MM/YYYY")
                total_lots = col1.number_input("Total Lots", min_value=0)
                rate = col2.number_input("Rate ₹", min_value=0.0)
                rice_type = col1.text_input("Rice Type")
                rice_agreement = col2.text_input("Rice Agreement")
                status = st.selectbox(
                    "Status", ["INITIATE_PHASE", "Pending", "Completed", "Cancelled"]
                )

                submitted = st.form_submit_button(
                    "✓ Submit Deal", use_container_width=True, type="primary"
                )
                if submitted:
                    try:
                        new_sauda = SaudaModel(
                            name=name,
                            broker_id=broker_id,
                            party_name=party_name,
                            purchase_date=datetime.combine(
                                purchase_date, datetime.min.time()
                            ),
                            total_lots=total_lots,
                            rate=rate,
                            rice_type=rice_type,
                            rice_agreement=rice_agreement,
                            status=status,
                        )
                        st.session_state["saudas"].append(new_sauda)
                        st.success(f"✓ Sauda '{name}' added successfully!")
                        st.session_state["add_sauda"] = False
                        st.rerun()
                    except ValidationError as e:
                        st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)

        # Display table with headers
        st.caption("Click 'View' to manage lots for each deal")

        # Table header
        header_cols = st.columns([2, 1, 1.5, 1, 1, 1, 1, 0.8])
        with header_cols[0]:
            st.markdown("**Name**")
        with header_cols[1]:
            st.markdown("**Broker ID**")
        with header_cols[2]:
            st.markdown("**Party Name**")
        with header_cols[3]:
            st.markdown("**Date**")
        with header_cols[4]:
            st.markdown("**Rice Type**")
        with header_cols[5]:
            st.markdown("**Rice Agreement**")
        with header_cols[6]:
            st.markdown("**Total Lots**")
        with header_cols[7]:
            st.markdown("**Action**")

        st.divider()

        # Table rows
        for idx, sauda in enumerate(st.session_state["saudas"]):
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1.5, 1, 1, 1, 1, 0.8])
            with col1:
                st.write(sauda.name)
            with col2:
                st.write(sauda.broker_id)
            with col3:
                st.write(sauda.party_name)
            with col4:
                st.write(sauda.purchase_date.strftime("%d-%m-%Y"))
            with col5:
                st.write(sauda.rice_type or "N/A")
            with col6:
                st.write(sauda.rice_agreement or "N/A")
            with col7:
                st.write(sauda.total_lots)
            with col8:
                if st.button("View →", key=f"view_{idx}", use_container_width=True):
                    st.session_state["selected_sauda"] = idx
                    st.rerun()

            if idx < len(st.session_state["saudas"]) - 1:
                st.divider()

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------- Broker Page ----------------
if page == "Brokers":
    # Custom Navbar for brokers
    st.markdown(
        f"""
    <div class="custom-navbar">
        <div>
            <div class="navbar-title">Brokers Management</div>
            <div class="navbar-subtitle">Manage broker information and contacts</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Add button row
    _, _, _, _, _, add_col = st.columns([1, 1, 1, 1, 1, 1])
    with add_col:
        button_label = (
            "➖ Close Form" if st.session_state["add_broker"] else "➕ Add New Broker"
        )
        if st.button(
            button_label, type="primary", key="broker_toggle", use_container_width=True
        ):
            st.session_state["add_broker"] = not st.session_state["add_broker"]
            st.rerun()

    if st.session_state["add_broker"]:
        with st.form("add_broker_form"):
            st.markdown("#### Add New Broker")
            col1, col2 = st.columns(2)
            broker_id = col1.text_input("Broker ID")
            name = col2.text_input("Broker Name")
            submitted = st.form_submit_button(
                "✓ Submit Broker", use_container_width=True, type="primary"
            )
            if submitted:
                try:
                    new_broker = BrokerModel(broker_id=broker_id, name=name)
                    st.session_state["brokers"].append(new_broker)
                    st.success(f"✓ Broker '{name}' added successfully!")
                    st.session_state["add_broker"] = False
                    st.rerun()
                except ValidationError as e:
                    st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)

    df_b = pd.DataFrame([b.model_dump() for b in st.session_state["brokers"]])
    st.write(style_dataframe(df_b).to_html(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
