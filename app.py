import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# FastAPI backend URL (make sure your FastAPI app is running)
FASTAPI_BASE_URL = "http://127.0.0.1:8001"

st.set_page_config(layout="wide") # Full width layout ke liye

# --- Helper Function to fetch transactions ---
def fetch_transactions():
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/transaction_detail")
        response.raise_for_status() # HTTP errors ke liye
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Error: FastAPI backend se connect nahi ho pa raha. Please make sure FastAPI app chal raha hai.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Transactions fetch karte waqt error: {e}")
        return None

# --- Page 1: Transaction Detail Page ---
def transaction_detail_page():
    st.markdown("<h1 style='text-align: center; color: #333;'>Office Transactions</h1>", unsafe_allow_html=True)

    # Top right corner par Add Transaction button
    col1, col2, col3 = st.columns([1, 1, 0.2]) # Adjust column widths for button positioning
    with col3:
        if st.button("+ Add Transaction", key="add_btn", help="Naya transaction add karein"):
            st.session_state.page = "add_transaction"
            st.rerun() # Page change karne ke liye rerun

    st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

    st.subheader("Transaction History")

    transactions = fetch_transactions()

    if transactions is None:
        st.info("Transactions fetch karte waqt koi problem hui. Please check server logs.")
        return

    if not transactions:
        st.info("Abhi tak koi transaction nahi hai. Naya transaction add karein.")
        return

    # Data ko display karne ke liye pandas DataFrame use kar rahe hain,
    # jisse table format accha dikhega.
    # Column order image ke hisaab se set kar rahe hain
    df = pd.DataFrame(transactions)
    
    # Ensure correct column order
    display_columns = ["date", "description", "credit", "debit", "running_balance"]
    df = df[display_columns]

    # Column names ko user-friendly banayein
    df.rename(columns={
        "date": "Date",
        "description": "Description",
        "credit": "Credit",
        "debit": "Debit",
        "running_balance": "Running Balance"
    }, inplace=True)

    # Optional: Format numeric columns for better readability (e.g., 2 decimal places)
    df["Credit"] = df["Credit"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
    df["Debit"] = df["Debit"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
    df["Running Balance"] = df["Running Balance"].apply(lambda x: f"{x:.2f}")

    # Display the DataFrame as a table
    st.dataframe(df, use_container_width=True, hide_index=True)


# --- Page 2: Add Transaction Page ---
def add_transaction_page():
    st.markdown("<h2 style='text-align: center;'>New Transaction</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

    with st.form("new_transaction_form", clear_on_submit=True):
        # st.subheader("Transaction Details")

        transaction_type = st.radio(
            "Transaction Type",
            ("Credit", "Debit"),
            horizontal=True,
            help="Transaction Credit hai ya Debit"
        )
        
        amount = st.number_input(
            "Amount",
            min_value=0.01, # Minimum value 0.01 se zyada
            value=None, # Default empty value
            step=0.01,
            format="%.2f",
            placeholder="Amount enter karein",
            help="Amount 0 se zyada hona chahiye"
        )
        
        description = st.text_area(
            "Description (Optional)",
            placeholder="Transaction description",
            height=80,
            help="Transaction ke baare mein likhein"
        )

        st.markdown("---") # Separator

        col_save, col_cancel = st.columns([1, 1])
        with col_save:
            submitted = st.form_submit_button("SAVE", type="primary")
        with col_cancel:
            if st.form_submit_button("CANCEL"):
                st.session_state.page = "transaction_detail"
                st.rerun()

        if submitted:
            if amount is None:
                st.error("Please enter a valid amount.")
            elif amount <= 0:
                st.error("Amount 0 se zyada hona chahiye.")
            else:
                payload = {
                    "transaction_type": transaction_type,
                    "amount": float(amount),
                    "description": description
                }
                
                try:
                    response = requests.post(f"{FASTAPI_BASE_URL}/add_transaction", json=payload)
                    response.raise_for_status() # HTTP errors ke liye

                    st.success("Transaction successfully added!")
                    st.session_state.page = "transaction_detail" # Redirect to detail page
                    st.rerun() # Rerun to show updated details
                except requests.exceptions.ConnectionError:
                    st.error("Error: FastAPI backend se connect nahi ho pa raha. Please make sure FastAPI app chal raha hai.")
                except requests.exceptions.HTTPError as e:
                    error_detail = e.response.json().get("detail", "Unknown error")
                    st.error(f"Transaction add karte waqt error: {error_detail}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Transaction add karte waqt error: {e}")

# --- Main Application Logic ---
if __name__ == "__main__":
    if "page" not in st.session_state:
        st.session_state.page = "transaction_detail" # Default page

    if st.session_state.page == "transaction_detail":
        transaction_detail_page()
    elif st.session_state.page == "add_transaction":
        add_transaction_page()