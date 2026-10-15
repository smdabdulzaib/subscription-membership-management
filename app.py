

from datetime import date, datetime
import os
from pathlib import Path
import pandas as pd
import streamlit as st

# Configure Streamlit page layout
st.set_page_config(
    page_title="SubSphere | Subscription & Membership Manager",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom SaaS Modern CSS
st.markdown(
    """
    <style>
        /* Base typography & containers */
        .main {
            background-color: #f8fafc;
        }
        h1, h2, h3, h4 {
            color: #0f172a;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Metric Cards */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            color: #64748b !important;
            text-transform: uppercase;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.45rem 1.2rem;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            border-color: #2563eb;
            color: #2563eb;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
        }
        section[data-testid="stSidebar"] .stMarkdown, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {
            color: #e2e8f0 !important;
        }
        
        /* Form Card */
        .form-card {
            background-color: #ffffff;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }

        /* Table styles */
        .dataframe {
            font-size: 0.9rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Import backend modules
from customers import (
    add_customer,
    delete_customer,
    get_all_customers,
    get_customer_by_id,
    update_customer,
)
from dashboard import render_dashboard_view
from database import (
    DB_CONFIG,
    auto_update_subscription_statuses,
    check_connection,
    init_database,
    update_db_config,
)
from invoices import get_all_invoices, get_invoice_by_id
from notifications import (
    batch_send_expiry_reminders,
    get_all_notifications,
    send_expiry_reminder,
)
from payments import get_all_payments, record_payment
from plans import add_plan, delete_plan, get_all_plans, get_plan_by_id, update_plan
from reports import (
    get_daily_revenue_df,
    get_monthly_renewals_and_cancellations_df,
    get_monthly_revenue_df,
    get_revenue_by_payment_method_df,
    get_revenue_by_plan_df,
    get_revenue_kpis,
    get_subscription_health_metrics,
)
from subscriptions import (
    cancel_subscription,
    create_subscription,
    downgrade_subscription,
    get_all_subscriptions,
    get_subscription_by_id,
    get_subscription_history,
    renew_subscription,
    upgrade_subscription,
)
from utils import (
    calculate_expiry_date,
    calculate_prorated_upgrade,
    calculate_remaining_days,
    calculate_renewal_dates,
    format_currency,
    format_date,
    generate_transaction_id,
    get_status_badge,
)

# -------------------------------------------------------------
# Session Authentication
# -------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")


def render_login():
    """Render professional login screen."""
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br/><br/>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background: white; padding: 35px 30px; border-radius: 14px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); text-align: center;">
                <div style="font-size: 2.8rem; margin-bottom: 8px;">💳</div>
                <h2 style="margin: 0; font-size: 1.6rem; color: #0f172a;">SubSphere Admin</h2>
                <p style="color: #64748b; font-size: 0.9rem; margin-top: 4px; margin-bottom: 24px;">Subscription & Membership Management Platform</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password", value="admin123")
            submit = st.form_submit_button("Sign In to Portal", use_container_width=True)

            if submit:
                if username == ADMIN_USER and password == ADMIN_PASS:
                    st.session_state["authenticated"] = True
                    st.success("Authentication successful! Loading dashboard...")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Default is admin / admin123.")

        st.caption("Default credentials: `admin` / `admin123` (configured via `.env`)")


# Check authentication
if not st.session_state["authenticated"]:
    render_login()
    st.stop()


# -------------------------------------------------------------
# Database Health Check & Auto-Status Update
# -------------------------------------------------------------
is_db_connected, db_status_msg = check_connection()
if is_db_connected:
    # Run auto-synchronization for expiry & active statuses
    auto_update_subscription_statuses()
else:
    st.warning(
        f"⚠️ **Database Connection Warning:** {db_status_msg}\n\n"
        "👉 Navigate to **Settings** in the sidebar to configure your MySQL connection or initialize the database schema."
    )


# -------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 10px 0 20px 0;">
            <span style="font-size: 2rem;">💳</span>
            <div>
                <h3 style="margin: 0; color: #ffffff !important; font-size: 1.25rem;">SubSphere</h3>
                <span style="font-size: 0.75rem; color: #94a3b8 !important;">v1.0.0 Enterprise</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    menu_options = [
        "Dashboard",
        "Customers",
        "Plans",
        "Subscriptions",
        "Payments",
        "Invoices",
        "Renewals",
        "Upgrade / Downgrade",
        "Cancellations",
        "Notifications",
        "Subscription History",
        "Revenue Reports",
        "Subscription Health",
        "Settings",
    ]
    menu_icons = {
        "Dashboard": "📊",
        "Customers": "👥",
        "Plans": "📦",
        "Subscriptions": "📜",
        "Payments": "💵",
        "Invoices": "🧾",
        "Renewals": "🔄",
        "Upgrade / Downgrade": "⚡",
        "Cancellations": "❌",
        "Notifications": "🔔",
        "Subscription History": "⏱️",
        "Revenue Reports": "📈",
        "Subscription Health": "🩺",
        "Settings": "⚙️",
    }

    selected_menu = st.radio(
        "Navigation",
        menu_options,
        format_func=lambda x: f"{menu_icons.get(x, '•')} {x}",
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border: 0; border-top: 1px solid #334155; margin: 20px 0;'/>", unsafe_allow_html=True)

    # DB Connection indicator in sidebar
    if is_db_connected:
        st.markdown("🟢 <span style='font-size: 0.8rem; color: #34d399;'>MySQL Online</span>", unsafe_allow_html=True)
    else:
        st.markdown("🔴 <span style='font-size: 0.8rem; color: #f87171;'>MySQL Disconnected</span>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()


# =============================================================
# 1. DASHBOARD
# =============================================================
if selected_menu == "Dashboard":
    if not is_db_connected:
        st.error("Database is not connected. Please initialize the database in the Settings tab.")
    else:
        render_dashboard_view()


# =============================================================
# 2. CUSTOMERS
# =============================================================
elif selected_menu == "Customers":
    st.markdown("<h2>👥 Customer Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Manage members, register profiles, and view active subscription linkages.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    tab_list, tab_add, tab_edit, tab_delete = st.tabs(["📋 Customer Directory", "➕ Register Customer", "✏️ Edit Customer", "⚠️ Deactivate / Delete"])

    with tab_list:
        c1, c2 = st.columns([2, 1])
        with c1:
            search_c = st.text_input("Search customers", placeholder="Search by name, email, or phone...")
        with c2:
            status_c = st.selectbox("Status Filter", ["All", "Active", "Inactive", "Suspended"], key="cust_status_filter")

        customers = get_all_customers(search_term=search_c, status_filter=status_c)

        if customers:
            df_cust = pd.DataFrame(customers)
            display_cols = ["customer_id", "name", "email", "phone", "registration_date", "account_status", "total_subscriptions", "active_subscriptions"]
            df_display = df_cust[display_cols].rename(columns={
                "customer_id": "ID",
                "name": "Name",
                "email": "Email",
                "phone": "Phone",
                "registration_date": "Registered",
                "account_status": "Status",
                "total_subscriptions": "Total Subs",
                "active_subscriptions": "Active Subs",
            })
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(customers)} registered members.")
        else:
            st.info("No customers found matching the criteria.")

    with tab_add:
        st.markdown("#### Register New Customer")
        with st.form("add_customer_form"):
            ac_name = st.text_input("Full Name *", placeholder="e.g. John Doe")
            ac_email = st.text_input("Email Address *", placeholder="e.g. john.doe@example.com")
            ac_phone = st.text_input("Phone Number *", placeholder="e.g. +91 9876543210")
            ac_reg_date = st.date_input("Registration Date", value=date.today())
            ac_status = st.selectbox("Account Status", ["Active", "Inactive", "Suspended"])
            submit_add = st.form_submit_button("Register Customer", use_container_width=True)

            if submit_add:
                ok, msg, cid = add_customer(ac_name, ac_email, ac_phone, ac_reg_date, ac_status)
                if ok:
                    st.success(f"Customer registered successfully! (Customer ID: #{cid})")
                    st.rerun()
                else:
                    st.error(msg)

    with tab_edit:
        st.markdown("#### Update Customer Details")
        all_custs = get_all_customers()
        if all_custs:
            cust_dict = {f"#{c['customer_id']} - {c['name']} ({c['email']})": c['customer_id'] for c in all_custs}
            sel_cust_label = st.selectbox("Select Customer to Edit", list(cust_dict.keys()), key="edit_cust_sel")
            target_cid = cust_dict[sel_cust_label]
            target_c = get_customer_by_id(target_cid)

            if target_c:
                with st.form("edit_cust_form"):
                    ec_name = st.text_input("Full Name", value=target_c["name"])
                    ec_email = st.text_input("Email", value=target_c["email"])
                    ec_phone = st.text_input("Phone", value=target_c["phone"])
                    status_idx = ["Active", "Inactive", "Suspended"].index(target_c.get("account_status", "Active"))
                    ec_status = st.selectbox("Account Status", ["Active", "Inactive", "Suspended"], index=status_idx)
                    submit_edit = st.form_submit_button("Save Changes", use_container_width=True)

                    if submit_edit:
                        ok, msg = update_customer(target_cid, ec_name, ec_email, ec_phone, ec_status)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.info("No customers available to edit.")

    with tab_delete:
        st.markdown("#### Safe Customer Deactivation / Removal")
        st.caption("Note: Customers with historical subscriptions will be deactivated rather than deleted to preserve billing records.")
        all_custs = get_all_customers()
        if all_custs:
            del_dict = {f"#{c['customer_id']} - {c['name']} ({c['email']})": c['customer_id'] for c in all_custs}
            sel_del_label = st.selectbox("Select Customer", list(del_dict.keys()), key="del_cust_sel")
            del_cid = del_dict[sel_del_label]

            if st.button("⚠️ Deactivate / Delete Customer", type="primary"):
                ok, msg = delete_customer(del_cid)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# =============================================================
# 3. PLANS
# =============================================================
elif selected_menu == "Plans":
    st.markdown("<h2>📦 Plan & Membership Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Configure subscription tiers, pricing, duration cycles, and entitlement features.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    tab_plans_view, tab_plans_add, tab_plans_edit = st.tabs(["📋 View Plans", "➕ Add New Plan", "✏️ Edit Plan"])

    with tab_plans_view:
        plans = get_all_plans()
        if plans:
            # Display plans in visual cards
            cols = st.columns(len(plans) if len(plans) <= 4 else 4)
            for i, p in enumerate(plans):
                col = cols[i % 4]
                with col:
                    badge_col = "#10b981" if p["status"] == "Active" else "#94a3b8"
                    st.markdown(
                        f"""
                        <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.04); margin-bottom: 15px; height: 100%;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <h3 style="margin: 0; font-size: 1.25rem; color: #1e293b;">{p['plan_name']}</h3>
                                <span style="background: {badge_col}22; color: {badge_col}; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 99px;">{p['status']}</span>
                            </div>
                            <div style="font-size: 1.7rem; font-weight: 700; color: #2563eb; margin-bottom: 4px;">{format_currency(p['price'])}</div>
                            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px;">Valid for <b>{p['duration_days']} days</b></div>
                            <div style="font-size: 0.82rem; color: #334155; min-height: 48px; border-top: 1px solid #f1f5f9; padding-top: 8px;">
                                {p['features'] or 'Standard features included.'}
                            </div>
                            <div style="margin-top: 12px; font-size: 0.8rem; color: #94a3b8;">
                                Active Subscribers: <b>{p.get('active_subscribers', 0)}</b>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No plans configured yet. Click 'Add New Plan' to create one.")

    with tab_plans_add:
        with st.form("add_plan_form"):
            p_name = st.text_input("Plan Name *", placeholder="e.g. Pro Annual")
            p_price = st.number_input("Price (₹) *", min_value=0.0, step=50.0, value=999.0)
            p_duration = st.number_input("Duration in Days *", min_value=1, step=1, value=30)
            p_features = st.text_area("Features (comma separated or bulleted)", placeholder="HD Streaming, 2 Devices, Priority Support")
            p_status = st.selectbox("Status", ["Active", "Inactive"])
            submit_plan = st.form_submit_button("Create Membership Plan", use_container_width=True)

            if submit_plan:
                ok, msg, pid = add_plan(p_name, p_price, p_duration, p_features, p_status)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_plans_edit:
        plans = get_all_plans()
        if plans:
            plan_map = {f"#{p['plan_id']} - {p['plan_name']} ({format_currency(p['price'])})": p['plan_id'] for p in plans}
            sel_p_lbl = st.selectbox("Select Plan to Edit", list(plan_map.keys()))
            target_pid = plan_map[sel_p_lbl]
            target_p = get_plan_by_id(target_pid)

            if target_p:
                with st.form("edit_plan_form"):
                    ep_name = st.text_input("Plan Name", value=target_p["plan_name"])
                    ep_price = st.number_input("Price (₹)", min_value=0.0, step=50.0, value=float(target_p["price"]))
                    ep_duration = st.number_input("Duration in Days", min_value=1, step=1, value=int(target_p["duration_days"]))
                    ep_features = st.text_area("Features", value=target_p.get("features") or "")
                    stat_idx = 0 if target_p["status"] == "Active" else 1
                    ep_status = st.selectbox("Status", ["Active", "Inactive"], index=stat_idx)

                    col_save, col_del = st.columns([1, 1])
                    with col_save:
                        submit_save_p = st.form_submit_button("Update Plan Details", use_container_width=True)

                if submit_save_p:
                    ok, msg = update_plan(target_pid, ep_name, ep_price, ep_duration, ep_features, ep_status)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

                if st.button("🗑️ Deactivate / Delete This Plan", key=f"del_plan_{target_pid}"):
                    ok, msg = delete_plan(target_pid)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# =============================================================
# 4. SUBSCRIPTIONS
# =============================================================
elif selected_menu == "Subscriptions":
    st.markdown("<h2>📜 Subscription Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Provision new subscriptions, track status lifecycles, and view live active contracts.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    tab_subs_list, tab_subs_new = st.tabs(["📋 All Subscriptions", "➕ Activate New Subscription"])

    with tab_subs_list:
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        with col_s1:
            search_s = st.text_input("Search Subscriptions", placeholder="Search by member, email, plan...")
        with col_s2:
            status_s = st.selectbox("Filter Status", ["All", "Active", "Expiring Soon", "Expired", "Cancelled"], key="sub_stat_filter")
        with col_s3:
            all_plans_raw = get_all_plans()
            plan_names = ["All"] + [p["plan_name"] for p in all_plans_raw]
            plan_s = st.selectbox("Filter Plan", plan_names, key="sub_plan_filter")

        subs = get_all_subscriptions(search_term=search_s, status_filter=status_s, plan_filter=plan_s)

        if subs:
            df_subs = pd.DataFrame(subs)
            display_cols = ["subscription_id", "customer_name", "customer_email", "plan_name", "start_date", "expiry_date", "status", "days_left"]
            df_display = df_subs[display_cols].rename(columns={
                "subscription_id": "Sub ID",
                "customer_name": "Customer",
                "customer_email": "Email",
                "plan_name": "Plan",
                "start_date": "Start Date",
                "expiry_date": "Expiry Date",
                "status": "Status",
                "days_left": "Days Left",
            })
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(subs)} subscriptions listed.")
        else:
            st.info("No subscriptions match your query.")

    with tab_subs_new:
        st.markdown("#### Activate New Subscription")
        st.caption("Workflow: Customer + Plan -> Auto Expiry Calculation -> Payment -> Invoice -> Subscription Activated")

        cust_list = get_all_customers()
        plans_list = get_all_plans(active_only=True)

        if not cust_list:
            st.warning("Please add at least one customer before activating a subscription.")
        elif not plans_list:
            st.warning("Please configure at least one active plan first.")
        else:
            cust_options = {f"#{c['customer_id']} - {c['name']} ({c['email']})": c['customer_id'] for c in cust_list}
            plan_options = {f"{p['plan_name']} (₹{p['price']} / {p['duration_days']} days)": p for p in plans_list}

            with st.form("new_sub_form"):
                sel_cust_str = st.selectbox("Select Customer *", list(cust_options.keys()))
                sel_plan_str = st.selectbox("Select Membership Plan *", list(plan_options.keys()))
                start_dt = st.date_input("Start Date", value=date.today())

                selected_plan_obj = plan_options[sel_plan_str]
                # Dynamic expiry preview
                auto_expiry = calculate_expiry_date(start_dt, selected_plan_obj["duration_days"])
                st.info(f"📅 **Calculated Expiry Date:** `{auto_expiry}` ({selected_plan_obj['duration_days']} days duration)")

                st.markdown("##### Payment Information")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    pay_method = st.selectbox("Payment Method", ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash"])
                with col_p2:
                    suggested_txn = generate_transaction_id()
                    txn_id_input = st.text_input("Transaction / Ref ID", value=suggested_txn)

                st.markdown(f"**Total Payable Amount:** `{format_currency(selected_plan_obj['price'])}`")
                sub_submit = st.form_submit_button("Activate & Process Payment", use_container_width=True)

                if sub_submit:
                    cid = cust_options[sel_cust_str]
                    pid = selected_plan_obj["plan_id"]
                    ok, msg, new_sub_id, pdf_path = create_subscription(
                        customer_id=cid,
                        plan_id=pid,
                        start_date=start_dt,
                        payment_method=pay_method,
                        transaction_id=txn_id_input,
                    )
                    if ok:
                        st.success(f"🎉 {msg}")
                        if pdf_path and Path(pdf_path).exists():
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="📄 Download Tax Invoice (PDF)",
                                    data=f.read(),
                                    file_name=Path(pdf_path).name,
                                    mime="application/pdf",
                                )
                        st.rerun()
                    else:
                        st.error(msg)


# =============================================================
# 5. PAYMENTS
# =============================================================
elif selected_menu == "Payments":
    st.markdown("<h2>💵 Payment Management</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>View payment logs, verify transaction IDs, and track settlement statuses.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        pay_search = st.text_input("Search Payments", placeholder="Search by Transaction ID, Customer, Email...")
    with c2:
        pay_status_filt = st.selectbox("Payment Status", ["All", "Success", "Pending", "Failed", "Refunded"])
    with c3:
        pay_meth_filt = st.selectbox("Payment Method", ["All", "UPI", "Credit Card", "Debit Card", "Net Banking", "Cash"])

    payments = get_all_payments(search_term=pay_search, status_filter=pay_status_filt, method_filter=pay_meth_filt)

    if payments:
        df_p = pd.DataFrame(payments)
        df_p["amount_formatted"] = df_p["amount"].apply(format_currency)
        cols_show = ["payment_id", "transaction_id", "customer_name", "plan_name", "amount_formatted", "payment_method", "payment_status", "payment_date", "invoice_number"]
        df_p_display = df_p[cols_show].rename(columns={
            "payment_id": "ID",
            "transaction_id": "Transaction ID",
            "customer_name": "Customer",
            "plan_name": "Plan",
            "amount_formatted": "Amount",
            "payment_method": "Method",
            "payment_status": "Status",
            "payment_date": "Timestamp",
            "invoice_number": "Invoice #",
        })
        st.dataframe(df_p_display, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(payments)} payment transactions.")
    else:
        st.info("No payment records found.")


# =============================================================
# 6. INVOICES
# =============================================================
elif selected_menu == "Invoices":
    st.markdown("<h2>🧾 Invoices & PDF Downloads</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Browse generated customer invoices and download professional PDF receipts.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    inv_search = st.text_input("Search Invoices", placeholder="Search by Invoice Number, Customer Name, Email...")
    invoices = get_all_invoices(search_term=inv_search)

    if invoices:
        col_list, col_preview = st.columns([1.5, 1])

        with col_list:
            df_inv = pd.DataFrame(invoices)
            df_inv["amount_str"] = df_inv["amount"].apply(format_currency)
            cols_disp = ["invoice_id", "invoice_number", "customer_name", "plan_name", "amount_str", "payment_method", "invoice_date"]
            df_disp = df_inv[cols_disp].rename(columns={
                "invoice_id": "ID",
                "invoice_number": "Invoice #",
                "customer_name": "Customer",
                "plan_name": "Plan",
                "amount_str": "Amount",
                "payment_method": "Payment Mode",
                "invoice_date": "Date",
            })
            st.dataframe(df_disp, use_container_width=True, hide_index=True)

        with col_preview:
            st.markdown("#### Invoice Action Center")
            inv_map = {f"{inv['invoice_number']} - {inv['customer_name']} ({format_currency(inv['amount'])})": inv for inv in invoices}
            sel_inv_str = st.selectbox("Select Invoice", list(inv_map.keys()))
            selected_inv = inv_map[sel_inv_str]

            st.markdown(
                f"""
                <div style="background: white; border-radius: 10px; padding: 18px; border: 1px solid #e2e8f0;">
                    <div style="font-weight: 700; font-size: 1.1rem; color: #1e293b;">{selected_inv['invoice_number']}</div>
                    <div style="color: #64748b; font-size: 0.85rem; margin-bottom: 12px;">Issued on {format_date(selected_inv['invoice_date'])}</div>
                    <p style="margin: 4px 0; font-size: 0.9rem;"><b>Billed To:</b> {selected_inv['customer_name']}</p>
                    <p style="margin: 4px 0; font-size: 0.9rem;"><b>Email:</b> {selected_inv['customer_email']}</p>
                    <p style="margin: 4px 0; font-size: 0.9rem;"><b>Plan:</b> {selected_inv['plan_name']}</p>
                    <p style="margin: 4px 0; font-size: 0.9rem;"><b>Total Paid:</b> <span style="color: #2563eb; font-weight: 700;">{format_currency(selected_inv['amount'])}</span></p>
                    <p style="margin: 4px 0; font-size: 0.9rem;"><b>Reference:</b> <code>{selected_inv['transaction_id']}</code></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Check if PDF exists on disk
            pdf_path = selected_inv.get("pdf_path")
            app_dir = Path(__file__).parent
            full_pdf_path = app_dir / pdf_path if pdf_path else None

            if full_pdf_path and full_pdf_path.exists():
                with open(full_pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                    st.download_button(
                        label=f"⬇️ Download {selected_inv['invoice_number']}.pdf",
                        data=pdf_bytes,
                        file_name=f"{selected_inv['invoice_number']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.caption("ℹ️ PDF document path registered. Click regenerate if file was moved.")
    else:
        st.info("No invoices found.")


# =============================================================
# 7. RENEWALS
# =============================================================
elif selected_menu == "Renewals":
    st.markdown("<h2>🔄 Subscription Renewal Workflow</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Extend active subscriptions or reactivate expired memberships with automated invoice creation.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    subs = get_all_subscriptions()
    eligible_subs = [s for s in subs if s["status"] in ("Active", "Expiring Soon", "Expired")]

    if not eligible_subs:
        st.info("No subscriptions currently eligible for renewal.")
    else:
        sub_opts = {
            f"Sub #{s['subscription_id']} | {s['customer_name']} | {s['plan_name']} (Expires: {format_date(s['expiry_date'])}) [{s['status']}]": s
            for s in eligible_subs
        }
        sel_sub_str = st.selectbox("Select Subscription to Renew", list(sub_opts.keys()))
        target_sub = sub_opts[sel_sub_str]

        plans_list = get_all_plans(active_only=True)
        plan_dict = {f"{p['plan_name']} (₹{p['price']} / {p['duration_days']} days)": p for p in plans_list}

        # Find current plan index
        curr_plan_idx = 0
        for i, p in enumerate(plans_list):
            if p["plan_id"] == target_sub["plan_id"]:
                curr_plan_idx = i
                break

        with st.form("renewal_form"):
            st.markdown("#### Renewal Configuration")
            sel_r_plan = st.selectbox("Renewal Plan Tier", list(plan_dict.keys()), index=curr_plan_idx)
            chosen_plan = plan_dict[sel_r_plan]

            is_expired = target_sub["status"] == "Expired" or (
                isinstance(target_sub["expiry_date"], date) and target_sub["expiry_date"] < date.today()
            )
            new_st, new_exp = calculate_renewal_dates(target_sub["expiry_date"], is_expired, chosen_plan["duration_days"])

            st.write(f"• Current Expiry: **{format_date(target_sub['expiry_date'])}**")
            st.write(f"• Renewal Cycle Start: **{format_date(new_st)}**")
            st.write(f"• **New Expiry Date:** **`{format_date(new_exp)}`**")
            st.write(f"• Renewal Fee: **`{format_currency(chosen_plan['price'])}`**")

            r_pay_mode = st.selectbox("Payment Method", ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash"])
            r_txn_id = st.text_input("Transaction ID", value=generate_transaction_id())
            r_remarks = st.text_input("Remarks", value="Customer membership renewal")

            submit_renew = st.form_submit_button("Confirm Renewal & Process Payment", use_container_width=True)

            if submit_renew:
                ok, msg, pdf_path = renew_subscription(
                    subscription_id=target_sub["subscription_id"],
                    plan_id=chosen_plan["plan_id"],
                    payment_method=r_pay_mode,
                    transaction_id=r_txn_id,
                    remarks=r_remarks,
                )
                if ok:
                    st.success(f"🎉 {msg}")
                    if pdf_path and Path(pdf_path).exists():
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="📄 Download Renewal Tax Invoice (PDF)",
                                data=f.read(),
                                file_name=Path(pdf_path).name,
                                mime="application/pdf",
                            )
                    st.rerun()
                else:
                    st.error(msg)


# =============================================================
# 8. UPGRADE / DOWNGRADE
# =============================================================
elif selected_menu == "Upgrade / Downgrade":
    st.markdown("<h2>⚡ Subscription Tier Modifications</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Upgrade with automatic prorated calculations or schedule graceful downgrades.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    tab_up, tab_down = st.tabs(["🚀 Prorated Upgrade", "🔻 Plan Downgrade"])

    subs = get_all_subscriptions()
    active_subs = [s for s in subs if s["status"] in ("Active", "Expiring Soon")]

    with tab_up:
        st.markdown("#### Upgrade to a Higher Tier (Prorated)")
        if not active_subs:
            st.info("No active subscriptions available to upgrade.")
        else:
            up_opts = {
                f"Sub #{s['subscription_id']} | {s['customer_name']} | Current: {s['plan_name']} (Expires: {format_date(s['expiry_date'])})": s
                for s in active_subs
            }
            sel_up_sub = st.selectbox("Select Subscription to Upgrade", list(up_opts.keys()), key="up_sub_sel")
            target_up = up_opts[sel_up_sub]

            # Available higher plans
            all_plans = get_all_plans(active_only=True)
            higher_plans = [p for p in all_plans if p["plan_id"] != target_up["plan_id"] and float(p["price"]) >= float(target_up["plan_price"])]

            if not higher_plans:
                st.info("This subscription is already on the highest tier!")
            else:
                h_plan_opts = {f"{p['plan_name']} (₹{p['price']} / {p['duration_days']} days)": p for p in higher_plans}
                sel_target_plan_str = st.selectbox("Select Higher Tier", list(h_plan_opts.keys()))
                target_new_plan = h_plan_opts[sel_target_plan_str]

                # Calculate prorated difference
                rem_days = calculate_remaining_days(target_up["expiry_date"])
                calc = calculate_prorated_upgrade(
                    current_plan_price=float(target_up["plan_price"]),
                    current_plan_duration=int(target_up["duration_days"]),
                    new_plan_price=float(target_new_plan["price"]),
                    new_plan_duration=int(target_new_plan["duration_days"]),
                    remaining_days=rem_days,
                )

                st.markdown(
                    f"""
                    <div style="background: white; border-radius: 10px; padding: 18px; border: 1px solid #e2e8f0; margin: 15px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #1e293b;">Prorated Calculation Breakdown</h4>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                            <div>Days Remaining:<br/><b>{rem_days} days</b></div>
                            <div>Current Plan Value Left:<br/><b>{format_currency(calc['current_remaining_value'])}</b></div>
                            <div>New Plan Remaining Cost:<br/><b>{format_currency(calc['new_remaining_value'])}</b></div>
                        </div>
                        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 12px 0;"/>
                        <div style="font-size: 1.1rem; color: #0f172a;">
                            Additional Amount Payable: <span style="color: #2563eb; font-weight: 700; font-size: 1.3rem;">{format_currency(calc['additional_amount'])}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form("confirm_upgrade_form"):
                    up_pay_mode = st.selectbox("Payment Method", ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash"])
                    up_txn = st.text_input("Transaction ID", value=generate_transaction_id())
                    up_remarks = st.text_input("Remarks", value="Prorated tier upgrade")
                    submit_up = st.form_submit_button("Confirm Upgrade & Charge Difference", use_container_width=True)

                    if submit_up:
                        ok, msg, charged, pdf_path = upgrade_subscription(
                            subscription_id=target_up["subscription_id"],
                            new_plan_id=target_new_plan["plan_id"],
                            payment_method=up_pay_mode,
                            transaction_id=up_txn,
                            remarks=up_remarks,
                        )
                        if ok:
                            st.success(f"🎉 {msg}")
                            if pdf_path and Path(pdf_path).exists():
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        label="📄 Download Upgrade Tax Invoice (PDF)",
                                        data=f.read(),
                                        file_name=Path(pdf_path).name,
                                        mime="application/pdf",
                                    )
                            st.rerun()
                        else:
                            st.error(msg)

    with tab_down:
        st.markdown("#### Plan Downgrade")
        st.caption("Business Rule: Downgrade becomes effective after the current paid cycle finishes.")

        if not active_subs:
            st.info("No active subscriptions.")
        else:
            down_opts = {
                f"Sub #{s['subscription_id']} | {s['customer_name']} | Current: {s['plan_name']} (Expires: {format_date(s['expiry_date'])})": s
                for s in active_subs
            }
            sel_down_sub = st.selectbox("Select Subscription to Downgrade", list(down_opts.keys()), key="down_sub_sel")
            target_down = down_opts[sel_down_sub]

            lower_plans = [p for p in all_plans if p["plan_id"] != target_down["plan_id"] and float(p["price"]) < float(target_down["plan_price"])]
            if not lower_plans:
                st.info("This is already the lowest plan tier.")
            else:
                l_plan_opts = {f"{p['plan_name']} (₹{p['price']} / {p['duration_days']} days)": p for p in lower_plans}
                sel_l_plan_str = st.selectbox("Select Target Downgrade Plan", list(l_plan_opts.keys()))
                chosen_lower = l_plan_opts[sel_l_plan_str]

                immediate = st.checkbox("Apply Immediately (No refund for remainder)", value=False)
                down_remarks = st.text_input("Downgrade Reason / Notes", value="Customer requested lower tier")

                if st.button("Confirm Downgrade", type="primary"):
                    ok, msg = downgrade_subscription(
                        subscription_id=target_down["subscription_id"],
                        new_plan_id=chosen_lower["plan_id"],
                        effective_immediately=immediate,
                        remarks=down_remarks,
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# =============================================================
# 9. CANCELLATIONS
# =============================================================
elif selected_menu == "Cancellations":
    st.markdown("<h2>❌ Subscription Cancellations</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Cancel memberships safely. Historical records and invoices are strictly preserved.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    subs = get_all_subscriptions()
    active_subs = [s for s in subs if s["status"] != "Cancelled"]

    if not active_subs:
        st.info("No cancellable subscriptions found.")
    else:
        can_opts = {
            f"Sub #{s['subscription_id']} | {s['customer_name']} | {s['plan_name']} (Expires: {format_date(s['expiry_date'])})": s
            for s in active_subs
        }
        sel_can_sub = st.selectbox("Select Subscription to Cancel", list(can_opts.keys()))
        target_can = can_opts[sel_can_sub]

        st.warning(
            f"⚠️ You are about to cancel subscription **#{target_can['subscription_id']}** for customer **{target_can['customer_name']}**.\n\n"
            "This will mark the contract as 'Cancelled' and log an immutable event in the audit trail. Customer and payment history will NOT be deleted."
        )

        can_remarks = st.text_area("Cancellation Reason *", placeholder="e.g. Customer relocating / financial constraints / non-usage")
        confirm_check = st.checkbox("I confirm that this cancellation has been approved.")

        if st.button("Proceed with Cancellation", type="primary", disabled=not confirm_check):
            if not can_remarks.strip():
                st.error("Please provide a reason for cancellation.")
            else:
                ok, msg = cancel_subscription(target_can["subscription_id"], remarks=can_remarks)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# =============================================================
# 10. NOTIFICATIONS
# =============================================================
elif selected_menu == "Notifications":
    st.markdown("<h2>🔔 Expiry Notifications & Email Alerts</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Automated SMTP renewal reminders with smart anti-duplication dispatch control.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    tab_dispatch, tab_notif_log = st.tabs(["🚀 Automated Dispatch", "📜 Notification History"])

    with tab_dispatch:
        col_cfg1, col_cfg2 = st.columns([1, 1.5])
        with col_cfg1:
            threshold_days = st.slider("Reminder Window (Days Before Expiry)", min_value=1, max_value=30, value=7)
            if st.button(f"⚡ Batch Dispatch Reminders (Within {threshold_days} Days)", type="primary"):
                with st.spinner("Dispatching notification emails..."):
                    res = batch_send_expiry_reminders(days=threshold_days)
                    st.success(
                        f"Dispatch Complete! Found {res['total']} eligible subscriptions. "
                        f"Sent: {res['sent']} | Skipped (already alerted today): {res['skipped']} | Failed: {res['failed']}"
                    )
                    st.rerun()

        with col_cfg2:
            st.markdown(
                """
                <div style="background: white; border-radius: 10px; padding: 18px; border: 1px solid #e2e8f0;">
                    <h4 style="margin: 0 0 8px 0; color: #1e293b;">Anti-Duplicate Protection</h4>
                    <p style="font-size: 0.85rem; color: #64748b; margin: 0;">
                        The system automatically prevents sending multiple reminder emails to the same subscriber on the same calendar day.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("#### Upcoming Expiring Subscriptions")
        subs = get_all_subscriptions()
        expiring = [s for s in subs if s["status"] in ("Active", "Expiring Soon") and 0 <= (s.get("days_left") or 99) <= threshold_days]

        if expiring:
            for s in expiring:
                with st.container():
                    c1, c2, c3, c4 = st.columns([2, 1.5, 1, 1])
                    with c1:
                        st.markdown(f"**{s['customer_name']}** ({s['customer_email']})")
                        st.caption(f"Plan: {s['plan_name']}")
                    with c2:
                        st.markdown(f"Expires: `{format_date(s['expiry_date'])}`")
                    with c3:
                        st.markdown(f"<span style='color: #f59e0b; font-weight: 700;'>{s['days_left']} days left</span>", unsafe_allow_html=True)
                    with c4:
                        if st.button("Send Alert", key=f"alert_btn_{s['subscription_id']}"):
                            ok, msg = send_expiry_reminder(s['subscription_id'], force_send=True)
                            if ok:
                                st.success(msg)
                            else:
                                st.warning(msg)
                            st.rerun()
                    st.markdown("<hr style='margin: 8px 0; border: 0; border-top: 1px solid #f1f5f9;'/>", unsafe_allow_html=True)
        else:
            st.info(f"No subscriptions expiring within the next {threshold_days} days.")

    with tab_notif_log:
        notif_filter = st.selectbox("Status Filter", ["All", "Sent", "Pending", "Failed"], key="notif_stat_filt")
        notifs = get_all_notifications(status_filter=notif_filter)
        if notifs:
            df_n = pd.DataFrame(notifs)
            cols_n = ["notification_id", "customer_name", "customer_email", "notification_type", "sent_at", "notification_status", "message"]
            df_n_disp = df_n[cols_n].rename(columns={
                "notification_id": "ID",
                "customer_name": "Customer",
                "customer_email": "Email",
                "notification_type": "Type",
                "sent_at": "Sent At",
                "notification_status": "Status",
                "message": "Message Content",
            })
            st.dataframe(df_n_disp, use_container_width=True, hide_index=True)
        else:
            st.info("No notifications logged.")


# =============================================================
# 11. SUBSCRIPTION HISTORY
# =============================================================
elif selected_menu == "Subscription History":
    st.markdown("<h2>⏱️ Immutable Audit Trail & History</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Full forensic audit log of all activations, renewals, upgrades, downgrades, and cancellations.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    col_h1, col_h2 = st.columns([1, 1])
    with col_h1:
        action_filter = st.selectbox("Filter by Action Type", ["All", "ACTIVATED", "UPGRADED", "DOWNGRADED", "RENEWED", "CANCELLED"])
    with col_h2:
        export_mode = st.empty()

    history = get_subscription_history(action_type=action_filter)

    if history:
        df_h = pd.DataFrame(history)
        df_h["amount_formatted"] = df_h["amount"].apply(format_currency)
        cols_h = ["history_id", "action_date", "customer_name", "action_type", "old_plan_name", "new_plan_name", "amount_formatted", "old_expiry_date", "new_expiry_date", "remarks"]
        df_h_disp = df_h[cols_h].rename(columns={
            "history_id": "ID",
            "action_date": "Timestamp",
            "customer_name": "Customer",
            "action_type": "Action",
            "old_plan_name": "Old Plan",
            "new_plan_name": "New Plan",
            "amount_formatted": "Amount (₹)",
            "old_expiry_date": "Old Expiry",
            "new_expiry_date": "New Expiry",
            "remarks": "Audit Remarks",
        })
        st.dataframe(df_h_disp, use_container_width=True, hide_index=True)

        # CSV Export
        csv_data = df_h_disp.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export Audit Log (CSV)",
            data=csv_data,
            file_name=f"subscription_history_{date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info("No audit records found matching the filter.")


# =============================================================
# 12. REVENUE REPORTS
# =============================================================
elif selected_menu == "Revenue Reports":
    st.markdown("<h2>📈 Revenue & Cashflow Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Financial reporting powered by Pandas & Plotly. Excludes failed/pending payments.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    kpi = get_revenue_kpis()

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Total Revenue", format_currency(kpi["total_revenue"]))
    with r2:
        st.metric("Monthly Revenue", format_currency(kpi["monthly_revenue"]))
    with r3:
        st.metric("Avg Transaction Value", format_currency(kpi["avg_transaction_value"]))
    with r4:
        st.metric("Total Paid Transactions", f"{kpi['total_transactions']:,}")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Revenue by Stream Breakdown
    c_st1, c_st2, c_st3 = st.columns(3)
    with c_st1:
        st.metric("New Activation Revenue", format_currency(kpi["activation_revenue"]))
    with c_st2:
        st.metric("Renewal Revenue", format_currency(kpi["renewal_revenue"]))
    with c_st3:
        st.metric("Upgrade Revenue", format_currency(kpi["upgrade_revenue"]))

    st.markdown("<hr style='border: 0; border-top: 1px solid #e2e8f0; margin: 25px 0;'/>", unsafe_allow_html=True)

    # Charts
    chart_col1, chart_col2 = st.columns([1.5, 1])

    with chart_col1:
        df_daily = get_daily_revenue_df(days=60)
        if not df_daily.empty:
            import plotly.express as px
            fig_daily = px.line(
                df_daily,
                x="payment_day",
                y="daily_revenue",
                title="Daily Revenue Trend (Last 60 Days)",
                markers=True,
                labels={"payment_day": "Date", "daily_revenue": "Revenue (₹)"},
            )
            fig_daily.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No daily payment data in range.")

    with chart_col2:
        df_meth = get_revenue_by_payment_method_df()
        if not df_meth.empty:
            import plotly.express as px
            fig_meth = px.pie(
                df_meth,
                names="payment_method",
                values="total_revenue",
                title="Revenue by Payment Channel",
                hole=0.45,
            )
            fig_meth.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_meth, use_container_width=True)


# =============================================================
# 13. SUBSCRIPTION HEALTH
# =============================================================
elif selected_menu == "Subscription Health":
    st.markdown("<h2>🩺 Subscription Health & Churn Metrics</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Monitor member retention health, churn velocity, and impending expirations.</p>", unsafe_allow_html=True)

    if not is_db_connected:
        st.error("Database connection required.")
        st.stop()

    health = get_subscription_health_metrics()

    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.metric("Total Members", f"{health['total_customers']:,}")
    with h2:
        st.metric("Active Subscriptions", f"{health['active_subs']:,}")
    with h3:
        st.metric("Churn Rate", f"{health['churn_rate']}%")
    with h4:
        st.metric("Expiring in 7 Days", f"{health['expiring_soon_subs']:,}")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Action Items for Admins
    st.markdown("#### 🚨 Action Required: High Priority Members")
    subs = get_all_subscriptions()
    critical = [s for s in subs if s["status"] == "Expiring Soon"]

    if critical:
        st.markdown(f"Found **{len(critical)}** members with subscriptions expiring this week:")
        df_crit = pd.DataFrame(critical)[["customer_name", "customer_email", "customer_phone", "plan_name", "expiry_date", "days_left"]]
        st.dataframe(df_crit, use_container_width=True, hide_index=True)
    else:
        st.success("All memberships are healthy! No contracts are expiring within the next 48 hours.")


# =============================================================
# 14. SETTINGS
# =============================================================
elif selected_menu == "Settings":
    st.markdown("<h2>⚙️ System Settings & MySQL Configuration</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Configure MySQL connection credentials, initialize schema, and seed demo records.</p>", unsafe_allow_html=True)

    # Live Status Card
    if is_db_connected:
        st.success(f"✅ **Database Connected:** {db_status_msg}")
    else:
        st.error(f"❌ **Connection Issue:** {db_status_msg}")

    tab_db_cfg, tab_schema, tab_smtp = st.tabs(["🔌 Database Connection", "🗄️ Schema & Demo Data", "✉️ SMTP Email Settings"])

    with tab_db_cfg:
        st.markdown("#### MySQL Connection Parameters")
        with st.form("db_config_form"):
            cfg_host = st.text_input("MySQL Host", value=DB_CONFIG["host"])
            cfg_port = st.number_input("MySQL Port", value=DB_CONFIG["port"], step=1)
            cfg_user = st.text_input("Username", value=DB_CONFIG["user"])
            cfg_pass = st.text_input("Password", value=DB_CONFIG["password"], type="password")
            cfg_name = st.text_input("Database Name", value=DB_CONFIG["database"])
            submit_cfg = st.form_submit_button("Test & Save Connection", use_container_width=True)

            if submit_cfg:
                update_db_config(
                    host=cfg_host,
                    port=cfg_port,
                    user=cfg_user,
                    password=cfg_pass,
                    database=cfg_name,
                )
                success, msg = check_connection()
                if success:
                    st.success(f"Connected successfully! {msg}")
                else:
                    st.warning(f"Connection test result: {msg}")
                st.rerun()

    with tab_schema:
        st.markdown("#### Database Initialization")
        st.caption("Creates the `subscription_management` database and runs the complete schema DDL (`sql/database.sql`).")

        col_init1, col_init2 = st.columns(2)
        with col_init1:
            if st.button("🚀 Initialize Schema + Seed Demo Data", type="primary", use_container_width=True):
                with st.spinner("Initializing schema and seeding demo data..."):
                    ok, msg = init_database(include_seed=True)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with col_init2:
            if st.button("⚡ Initialize Empty Tables Only (No Seed)", use_container_width=True):
                with st.spinner("Creating empty schema..."):
                    ok, msg = init_database(include_seed=False)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with tab_smtp:
        st.markdown("#### Email / SMTP Configuration")
        st.caption("Used to dispatch automatic expiry reminders and receipts.")
        st.text_input("SMTP Host", value=os.getenv("SMTP_HOST", "smtp.gmail.com"), disabled=True)
        st.text_input("SMTP Port", value=os.getenv("SMTP_PORT", "587"), disabled=True)
        st.text_input("SMTP Username", value=os.getenv("SMTP_USERNAME", "Not configured (simulated mode active)"), disabled=True)
        st.caption("💡 To enable real SMTP dispatch, set `SMTP_USERNAME` and `SMTP_PASSWORD` in your `.env` file.")
