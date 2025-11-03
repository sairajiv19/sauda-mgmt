import streamlit as st
import aiohttp
import asyncio
from datetime import datetime

# ---------------- Set Page Config FIRST ----------------
st.set_page_config(page_title="Sauda Management System", layout="wide")

# ---------------- API Configuration ----------------
BASE_URL = "http://localhost:8000"

# ---------------- API Helper Functions ----------------
async def fetch_all_deals_async():
    """Fetch all deals from API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/deals/read/all") as response:
                response.raise_for_status()
                data = await response.json()
                return data["response"]
    except Exception as e:
        st.error(f"Error fetching deals: {str(e)}")
        return []

async def fetch_all_brokers_async():
    """Fetch all brokers from API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/brokers/read/all") as response:
                response.raise_for_status()
                data = await response.json()
                return data["response"]
    except Exception as e:
        st.error(f"Error fetching brokers: {str(e)}")
        return []

async def fetch_deal_lots_async(public_deal_id: str):
    """Fetch all lots for a specific deal"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/deals/read/{public_deal_id}/lot/all") as response:
                response.raise_for_status()
                data = await response.json()
                return data["response"]
    except Exception as e:
        st.error(f"Error fetching lots: {str(e)}")
        return []

async def fetch_lot_details_async(public_deal_id: str, public_lot_id: str):
    """Fetch details of a specific lot"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/deals/read/{public_deal_id}/lot/{public_lot_id}") as response:
                response.raise_for_status()
                data = await response.json()
                return data["response"]
    except Exception as e:
        st.error(f"Error fetching lot details: {str(e)}")
        return None

async def create_deal_async(deal_data: dict):
    """Create a new deal"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/deals/create/", json=deal_data) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except Exception as e:
        st.error(f"Error creating deal: {str(e)}")
        return None

async def create_broker_async(broker_data: dict):
    """Create a new broker"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/brokers/create/", json=broker_data) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except Exception as e:
        st.error(f"Error creating broker: {str(e)}")
        return None

async def update_lot_async(public_deal_id: str, public_lot_id: str, update_data: dict):
    """Update a single lot"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{BASE_URL}/deals/update/{public_deal_id}/lots/{public_lot_id}/update",
                json=update_data
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except Exception as e:
        st.error(f"Error updating lot: {str(e)}")
        return None

# ---------------- Session State Initialization ----------------
if "selected_sauda_id" not in st.session_state:
    st.session_state["selected_sauda_id"] = None
if "selected_lot_id" not in st.session_state:
    st.session_state["selected_lot_id"] = None
if "add_sauda" not in st.session_state:
    st.session_state["add_sauda"] = False
if "add_broker" not in st.session_state:
    st.session_state["add_broker"] = False
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = False
if "show_confirmation" not in st.session_state:
    st.session_state["show_confirmation"] = False
if "pending_changes" not in st.session_state:
    st.session_state["pending_changes"] = {}
if "brokers_cache" not in st.session_state:
    st.session_state["brokers_cache"] = None
if "refresh_brokers" not in st.session_state:
    st.session_state["refresh_brokers"] = False

# ---------------- Custom CSS ----------------
st.markdown(
    """
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .main {
        background-color: #f0f2f6;
    }
    
    .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 2rem;
    }
    
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
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    div[data-testid="column"] > div > div > button {
        height: 80px;
        font-size: 16px;
        font-weight: 600;
    }
    
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

# ---------------- Sidebar Navigation ----------------
page = st.sidebar.selectbox("Navigate", ["Sauda Deals", "Brokers"], index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Sauda Management System © 2025")

# ---------------- Main Async Logic ----------------
async def main():
    # Fetch and cache brokers if needed
    if st.session_state["brokers_cache"] is None or st.session_state["refresh_brokers"]:
        st.session_state["brokers_cache"] = await fetch_all_brokers_async()
        st.session_state["refresh_brokers"] = False
    
    brokers = st.session_state["brokers_cache"]
    
    # ---------------- Sauda Deals Page ----------------
    if page == "Sauda Deals":
        # Check if viewing a specific deal
        if st.session_state["selected_sauda_id"] is not None:
            deals = await fetch_all_deals_async()
            sauda = next((d for d in deals if d["public_id"] == st.session_state["selected_sauda_id"]), None)
            
            if not sauda:
                st.error("Deal not found")
                st.session_state["selected_sauda_id"] = None
                st.rerun()

            # Custom Navbar
            st.markdown(
                f"""
            <div class="custom-navbar">
                <div>
                    <div class="navbar-title">{sauda['name']}</div>
                    <div class="navbar-subtitle">Sauda Details & Lot Management</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Smaller back button
            back_col, _, _, _, _, _ = st.columns([1, 1, 1, 1, 1, 1])
            with back_col:
                if st.button("← Back to Saudas", use_container_width=True, type="secondary"):
                    st.session_state["selected_sauda_id"] = None
                    st.session_state["selected_lot_id"] = None
                    st.session_state["edit_mode"] = False
                    st.rerun()

            # Display sauda details
            st.markdown("#### Sauda Information")
            info_col1, info_col2, info_col3, info_col4, info_col5, info_col6 = st.columns(6)
            with info_col1:
                st.metric("Party Name", sauda["party_name"])
            with info_col2:
                st.metric("Broker ID", sauda["broker_id"])
            with info_col3:
                st.metric("Rate", f"₹{sauda['rate']:,.2f}")
            with info_col4:
                st.metric("Status", sauda["status"])
            with info_col5:
                st.metric("Rice Type", sauda.get("rice_type") or "N/A")
            with info_col6:
                st.metric("Agreement", sauda.get("rice_agreement") or "N/A")

            # Check if viewing lot details
            if st.session_state["selected_lot_id"] is not None:
                lot_data = await fetch_lot_details_async(sauda["public_id"], st.session_state["selected_lot_id"])
                
                if not lot_data:
                    st.error("Lot not found")
                    st.session_state["selected_lot_id"] = None
                    st.rerun()

                # Back and Edit buttons
                back_col, _, _, _, edit_col = st.columns([1, 1, 1, 1, 1])
                with back_col:
                    if st.button("← Back to Lots", use_container_width=True, type="secondary", key="back_to_lots"):
                        st.session_state["selected_lot_id"] = None
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
                        if st.button("❌ Cancel", use_container_width=True, type="secondary"):
                            st.session_state["edit_mode"] = False
                            st.session_state["pending_changes"] = {}
                            st.session_state["show_confirmation"] = False
                            st.rerun()

                st.markdown(f"<h2 style='text-align: center;'>Lot → {lot_data.get('rice_lot_no', 'N/A')}</h2>", unsafe_allow_html=True)

                if st.session_state["edit_mode"]:
                    # Edit mode
                    st.markdown("#### Edit Lot Details")

                    col1, col2 = st.columns(2)

                    rice_lot_no = col1.text_input(
                        "Rice Lot No", value=lot_data.get("rice_lot_no", ""), key="edit_rice_lot_no"
                    )

                    st.markdown("---")
                    st.markdown("**FRK Details**")

                    frk = st.checkbox("FRK", value=lot_data.get("frk", False), key="edit_frk")

                    frk_via = ""
                    frk_qty = 0.0
                    frk_date = None
                    
                    if frk:
                        frk_col1, frk_col2 = st.columns(2)
                        frk_bheja = lot_data.get("frk_bheja", {})
                        frk_via = frk_col1.text_input(
                            "FRK Via",
                            value=frk_bheja.get('frk_via', '') if frk_bheja else "",
                            key="edit_frk_via"
                        )
                        frk_qty = frk_col2.number_input(
                            "FRK Qty",
                            value=float(frk_bheja.get('frk_qty', 0)) if frk_bheja else 0.0,
                            min_value=0.0,
                            key="edit_frk_qty"
                        )
                        frk_date_str = frk_bheja.get('frk_date') if frk_bheja else None
                        if frk_date_str:
                            try:
                                frk_date = datetime.fromisoformat(frk_date_str.replace('Z', '+00:00')).date()
                            except:
                                frk_date = None
                        
                        frk_date = frk_col1.date_input(
                            "FRK Date",
                            value=frk_date,
                            key="edit_frk_date",
                            format="DD/MM/YYYY"
                        )

                    st.markdown("---")
                    st.markdown("**Purchase Details**")

                    purchase_col1, purchase_col2 = st.columns(2)
                    
                    rice_pass_date_str = lot_data.get("rice_pass_date")
                    rice_pass_date = None
                    if rice_pass_date_str:
                        try:
                            rice_pass_date = datetime.fromisoformat(rice_pass_date_str.replace('Z', '+00:00')).date()
                        except:
                            pass
                    
                    rice_pass_date = purchase_col1.date_input(
                        "Rice Pass Date",
                        value=rice_pass_date,
                        key="edit_rice_pass_date",
                        format="DD/MM/YYYY"
                    )
                    rice_deposit_centre = purchase_col2.text_input(
                        "Rice Deposit Centre", value=lot_data.get("rice_deposit_centre", ""), key="edit_deposit"
                    )
                    qtl = purchase_col1.number_input(
                        "Quantity (Qtl)", value=float(lot_data.get("qtl", 0)), min_value=0.0, key="edit_qtl"
                    )
                    rice_bags_quantity = purchase_col2.number_input(
                        "Rice Bags Quantity",
                        value=int(lot_data.get("rice_bags_quantity", 0)),
                        min_value=0,
                        key="edit_bags"
                    )
                    net_rice_bought = purchase_col1.number_input(
                        "Net Rice Bought",
                        value=float(lot_data.get("net_rice_bought", 0)),
                        min_value=0.0,
                        key="edit_net_rice"
                    )

                    st.markdown("---")
                    st.markdown("**Cost Details**")

                    cost_col1, cost_col2 = st.columns(2)
                    moisture_cut = cost_col1.number_input(
                        "Moisture Cut",
                        value=float(lot_data.get("moisture_cut", 0)),
                        min_value=0.0,
                        key="edit_moisture"
                    )
                    qi_expense = cost_col2.number_input(
                        "QI Expense", value=float(lot_data.get("qi_expense", 0)), min_value=0.0, key="edit_qi"
                    )
                    lot_dalali_expense = cost_col1.number_input(
                        "Dalali Expense",
                        value=float(lot_data.get("lot_dalali_expense", 0)),
                        min_value=0.0,
                        key="edit_dalali"
                    )
                    other_expenses = cost_col2.number_input(
                        "Other Costs", value=float(lot_data.get("other_expenses", 0)), min_value=0.0, key="edit_other"
                    )
                    brokerage = cost_col1.number_input(
                        "Brokerage", value=float(lot_data.get("brokerage", 0)), min_value=0.0, key="edit_brokerage"
                    )

                    st.markdown("---")
                    
                    if st.button("💾 Save Changes", use_container_width=True, type="primary", key="save_btn"):
                        update_payload = {
                            "rice_lot_no": rice_lot_no,
                            "frk": frk,
                            "rice_deposit_centre": rice_deposit_centre,
                            "qtl": qtl,
                            "rice_bags_quantity": rice_bags_quantity,
                            "net_rice_bought": net_rice_bought,
                            "moisture_cut": moisture_cut,
                            "qi_expense": qi_expense,
                            "lot_dalali_expense": lot_dalali_expense,
                            "other_expenses": other_expenses,
                            "brokerage": brokerage,
                        }
                        
                        if frk:
                            update_payload["frk_bheja"] = {
                                "frk_via": frk_via,
                                "frk_qty": frk_qty,
                                "frk_date": datetime.combine(frk_date, datetime.min.time()).isoformat() if frk_date else None
                            }
                        
                        if rice_pass_date:
                            update_payload["rice_pass_date"] = datetime.combine(rice_pass_date, datetime.min.time()).isoformat()
                        
                        st.session_state["pending_changes"] = update_payload
                        st.session_state["show_confirmation"] = True
                        st.rerun()

                else:
                    # Display mode
                    st.markdown("#### FRK Details")
                    st.markdown(f"**FRK Status:** {'FRK' if lot_data.get('frk') else 'Non FRK'}")

                    if lot_data.get("frk") and lot_data.get("frk_bheja"):
                        frk_bheja = lot_data["frk_bheja"]
                        st.markdown(f"**FRK Via:** {frk_bheja.get('frk_via', 'N/A')}")
                        st.markdown(f"**FRK Qty:** {frk_bheja.get('frk_qty', 0)}")
                        frk_date_str = frk_bheja.get('frk_date')
                        if frk_date_str:
                            try:
                                frk_date_obj = datetime.fromisoformat(frk_date_str.replace('Z', '+00:00'))
                                st.markdown(f"**FRK Date:** {frk_date_obj.strftime('%d-%m-%Y')}")
                            except:
                                st.markdown("**FRK Date:** N/A")

                    st.markdown("---")
                    st.markdown("#### Purchase Details")
                    rice_pass_str = lot_data.get("rice_pass_date")
                    if rice_pass_str:
                        try:
                            rice_pass_obj = datetime.fromisoformat(rice_pass_str.replace('Z', '+00:00'))
                            st.markdown(f"**Rice Pass Date:** {rice_pass_obj.strftime('%d-%m-%Y')}")
                        except:
                            st.markdown("**Rice Pass Date:** N/A")
                    else:
                        st.markdown("**Rice Pass Date:** N/A")
                        
                    st.markdown(f"**Rice Deposit Centre:** {lot_data.get('rice_deposit_centre') or 'N/A'}")
                    st.markdown(f"**Quantity (Qtl):** {lot_data.get('qtl', 0)}")
                    st.markdown(f"**Rice Bags Quantity:** {lot_data.get('rice_bags_quantity', 0)}")
                    st.markdown(f"**Net Rice Bought:** {lot_data.get('net_rice_bought', 0)}")

                    st.markdown("---")
                    st.markdown("#### Cost Details")
                    st.markdown(f"**Moisture Cut:** ₹{lot_data.get('moisture_cut', 0):,.2f}")
                    st.markdown(f"**QI Expense:** ₹{lot_data.get('qi_expense', 0):,.2f}")
                    st.markdown(f"**Dalali Expense:** ₹{lot_data.get('lot_dalali_expense', 0):,.2f}")
                    st.markdown(f"**Other Costs:** ₹{lot_data.get('other_expenses', 0):,.2f}")
                    st.markdown(f"**Brokerage:** ₹{lot_data.get('brokerage', 0):,.2f}")

                # Confirmation dialog
                if st.session_state["show_confirmation"]:
                    st.markdown("---")
                    st.warning("⚠️ Are you sure you want to save these changes?")
                    conf_col1, conf_col2 = st.columns(2)
                    with conf_col1:
                        if st.button("✓ Yes, Save Changes", use_container_width=True, type="primary", key="confirm_yes"):
                            result = await update_lot_async(
                                sauda["public_id"],
                                st.session_state["selected_lot_id"],
                                st.session_state["pending_changes"]
                            )
                            if result:
                                st.success("✓ Changes saved successfully!")
                                st.session_state["show_confirmation"] = False
                                st.session_state["edit_mode"] = False
                                st.session_state["pending_changes"] = {}
                                st.rerun()
                    with conf_col2:
                        if st.button("✗ No, Cancel", use_container_width=True, type="secondary", key="confirm_no"):
                            st.session_state["show_confirmation"] = False
                            st.session_state["pending_changes"] = {}
                            st.rerun()

            else:
                # Show lot selection grid
                lots = await fetch_deal_lots_async(sauda["public_id"])
                
                if lots:
                    st.markdown(f"#### Lot Selection ({len(lots)} lots available)")
                    st.caption("Click on a lot to view details")

                    cols_per_row = 6
                    for i in range(0, len(lots), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j in range(cols_per_row):
                            if i + j >= len(lots):
                                break
                            
                            lot = lots[i + j]
                            if not isinstance(lot, dict):
                                continue
                                
                            with cols[j]:
                                lot_display = lot.get("rice_lot_no") or f"Lot {i+j+1}"
                                lot_id = lot.get("public_id")
                                
                                if lot_id and st.button(
                                    lot_display,
                                    key=f"lot_btn_{i}_{j}",
                                    use_container_width=True,
                                    type="primary",
                                ):
                                    st.session_state["selected_lot_id"] = str(lot_id)
                                    st.rerun()
                else:
                    st.info("No lots found for this deal")

        else:
            # Main deals list view
            st.markdown(
                """
                <div class="custom-navbar">
                    <div>
                        <div class="navbar-title">Sauda Management Overview</div>
                        <div class="navbar-subtitle">Manage and track all your saudas</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Add button
            _, _, _, _, _, add_col = st.columns([1, 1, 1, 1, 1, 1])
            with add_col:
                button_label = "➖ Close Form" if st.session_state["add_sauda"] else "➕ Add New Deal"
                if st.button(button_label, type="primary", key="sauda_toggle", use_container_width=True):
                    st.session_state["add_sauda"] = not st.session_state["add_sauda"]
                    st.rerun()

            # Add deal form
            if st.session_state["add_sauda"]:
                with st.form("add_sauda_form"):
                    st.markdown("#### Add New Sauda")
                    col1, col2 = st.columns(2)
                    
                    broker_options = [broker["broker_id"] for broker in brokers] if brokers else []
                    
                    name = col1.text_input("Deal Name")
                    broker_id = col2.selectbox("Broker ID", options=broker_options) if broker_options else col2.text_input("Broker ID")
                    party_name = col1.text_input("Party Name")
                    purchase_date = col2.date_input("Purchase Date", datetime.now(), format="DD/MM/YYYY")
                    total_lots = col1.number_input("Total Lots", min_value=0)
                    rate = col2.number_input("Rate ₹", min_value=0.0)
                    rice_type = col1.text_input("Rice Type")
                    rice_agreement = col2.text_input("Rice Agreement")

                    submitted = st.form_submit_button("✓ Submit Deal", use_container_width=True, type="primary")
                    if submitted:
                        deal_payload = {
                            "name": name,
                            "broker_id": broker_id,
                            "party_name": party_name,
                            "purchase_date": datetime.combine(purchase_date, datetime.min.time()).isoformat(),
                            "total_lots": total_lots,
                            "rate": rate,
                            "rice_type": rice_type,
                            "rice_agreement": rice_agreement
                        }
                        
                        result = await create_deal_async(deal_payload)
                        if result:
                            st.success(f"✓ Sauda '{name}' added successfully!")
                            st.session_state["add_sauda"] = False
                            st.rerun()

            # Fetch and display all deals
            deals = await fetch_all_deals_async()

            if deals:
                st.caption(f"Total Deals: {len(deals)} | Click 'View' to manage lots")
                
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
                for idx, sauda in enumerate(deals):
                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1.5, 1, 1, 1, 1, 0.8])
                    with col1:
                        st.write(sauda.get("name", "N/A"))
                    with col2:
                        st.write(sauda.get("broker_id", "N/A"))
                    with col3:
                        st.write(sauda.get("party_name", "N/A"))
                    with col4:
                        purchase_date = sauda.get("purchase_date", "")
                        if purchase_date:
                            try:
                                date_obj = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                                st.write(date_obj.strftime("%d-%m-%Y"))
                            except:
                                st.write(purchase_date)
                        else:
                            st.write("N/A")
                    with col5:
                        st.write(sauda.get("rice_type") or "N/A")
                    with col6:
                        st.write(sauda.get("rice_agreement") or "N/A")
                    with col7:
                        st.write(sauda.get("total_lots", 0))
                    with col8:
                        if st.button("View →", key=f"view_{idx}", use_container_width=True):
                            st.session_state["selected_sauda_id"] = sauda["public_id"]
                            st.rerun()
                    
                    if idx < len(deals) - 1:
                        st.divider()
            else:
                st.info("No deals found. Add a new deal to get started!")
    
    # ---------------- Brokers Page ----------------
    elif page == "Brokers":
        st.markdown(
            """
            <div class="custom-navbar">
                <div>
                    <div class="navbar-title">Brokers Management</div>
                    <div class="navbar-subtitle">Manage broker information and contacts</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Add button
        _, _, _, _, _, add_col = st.columns([1, 1, 1, 1, 1, 1])
        with add_col:
            if st.button(
                "➖ Close Form" if st.session_state["add_broker"] else "➕ Add New Broker",
                type="primary",
                key="broker_toggle",
                use_container_width=True,
            ):
                st.session_state["add_broker"] = not st.session_state["add_broker"]
                st.rerun()

        # Add broker form
        if st.session_state["add_broker"]:
            with st.form("add_broker_form"):
                st.markdown("#### Add New Broker")
                col1, col2 = st.columns(2)
                name = col1.text_input("Broker Name")
                broker_id_str = col2.text_input("Broker ID")
                
                if st.form_submit_button("✓ Submit Broker", use_container_width=True, type="primary"):
                    broker_payload = {
                        "name": name,
                        "broker_id": broker_id_str
                    }
                    result = await create_broker_async(broker_payload)
                    if result:
                        st.success(f"✓ Broker '{name}' added successfully!")
                        st.session_state["add_broker"] = False
                        st.session_state["refresh_brokers"] = True  # Trigger broker refresh
                        st.rerun()

        # Display brokers
        deals = await fetch_all_deals_async()
        
        if brokers:
            st.caption(f"Total Brokers: {len(brokers)}")
            
            # Table header
            header_cols = st.columns([1, 1, 1, 2])
            with header_cols[0]:
                st.markdown("**Broker Name**")
            with header_cols[1]:
                st.markdown("**Broker ID**")
            with header_cols[2]:
                st.markdown("**Total Saudas**")
            
            st.divider()
            
            # Table rows
            for idx, broker in enumerate(brokers):
                col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
                with col1:
                    st.write(broker.get("name", "N/A"))
                with col2:
                    st.write(str(broker.get("broker_id", "N/A")))
                with col3:
                    # Count saudas linked to this broker
                    sauda_count = sum(1 for s in deals if s.get("broker_id") == broker.get("broker_id"))
                    st.write(sauda_count)
                
                if idx < len(brokers) - 1:
                    st.divider()
        else:
            st.info("No brokers found. Add a new broker to get started!")

# Run the async main function
asyncio.run(main())
