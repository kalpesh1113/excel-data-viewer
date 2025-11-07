import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Excel Data Viewer", layout="wide")

st.title("📘 Excel Data Viewer (Online with Log Resume)")
st.markdown("Upload Excel, mark each record ✅ Done or ⏭ Skip with reason. You can pause anytime and later resume from log.")
st.markdown("---")

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = None
    st.session_state.current_index = 0
    st.session_state.done_records = set()
    st.session_state.skipped_records = set()
    st.session_state.log_data = []


def save_log_to_memory(cons_no, action, reason=None):
    """Store log in session memory"""
    log_entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "CONS_NO": cons_no,
        "Action": action,
        "Reason": reason or ""
    }
    st.session_state.log_data.append(log_entry)


def jump_to_next_unprocessed():
    """Move pointer to next unprocessed record"""
    data = st.session_state.data
    while st.session_state.current_index < len(data):
        cons_no = str(data.iloc[st.session_state.current_index].get("CONS_NO", f"Row{st.session_state.current_index+1}"))
        if cons_no not in st.session_state.done_records and cons_no not in st.session_state.skipped_records:
            break
        st.session_state.current_index += 1


def jump_to_previous_unprocessed():
    """Move pointer to previous unprocessed record"""
    data = st.session_state.data
    while st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        cons_no = str(data.iloc[st.session_state.current_index].get("CONS_NO", f"Row{st.session_state.current_index+1}"))
        if cons_no not in st.session_state.done_records and cons_no not in st.session_state.skipped_records:
            break


uploaded_excel = st.file_uploader("📂 Upload Excel File", type=["xlsx", "xls"])
uploaded_log = st.file_uploader("🧾 (Optional) Upload Log File to Resume Progress", type=["csv", "txt"])

if uploaded_excel:
    df = pd.read_excel(uploaded_excel, dtype=str).fillna("")
    st.session_state.data = df

    # Resume from log if provided
    if uploaded_log:
        log_df = pd.read_csv(uploaded_log) if uploaded_log.name.endswith(".csv") else None
        if log_df is not None and "CONS_NO" in log_df.columns and "Action" in log_df.columns:
            for _, row in log_df.iterrows():
                cons = str(row["CONS_NO"])
                act = row["Action"]
                if act.startswith("DONE"):
                    st.session_state.done_records.add(cons)
                elif act.startswith("SKIPPED"):
                    st.session_state.skipped_records.add(cons)
            st.session_state.log_data = log_df.to_dict("records")
            st.success("✅ Progress resumed from uploaded log file.")
        # Jump to next unprocessed record automatically
        st.session_state.current_index = 0
        jump_to_next_unprocessed()

    df = st.session_state.data
    total = len(df)
    done = len(st.session_state.done_records)
    skipped = len(st.session_state.skipped_records)

    st.markdown(f"### Summary: Total {total} | ✅ Done {done} | ⏭ Skipped {skipped}")
    st.markdown("---")

    if st.session_state.current_index >= len(df):
        st.success("🎉 Job Completed Successfully!")
        csv_data = pd.DataFrame(st.session_state.log_data).to_csv(index=False)
        st.download_button(
            "📥 Download Log File",
            data=csv_data,
            file_name=f"{uploaded_excel.name}_log.csv",
            mime="text/csv"
        )
    else:
        record = df.iloc[st.session_state.current_index]
        st.subheader(f"🔹 Record {st.session_state.current_index + 1} / {len(df)}")

        headers = record.index.tolist()
        values = record.values.tolist()
        group_size = 5
        row = 0

        # Display in styled 5-column grid (bold + colored like PyQt)
        for i in range(0, len(headers), group_size):
            cols = st.columns(group_size * 2)
            for j in range(group_size):
                if i + j < len(headers):
                    header = str(headers[i + j])
                    value = str(values[i + j])

                    if row < 2:  # highlight first 2 rows
                        header_html = f"<div style='background-color:#FFD54F;padding:6px;border:1px solid gray;font-weight:bold;color:black;'>{header}</div>"
                        value_html = f"<div style='background-color:#FFF9C4;padding:6px;border:1px solid gray;font-weight:bold;color:black;'>{value}</div>"
                    else:
                        header_html = f"<div style='background-color:#2F4F4F;padding:6px;border:1px solid black;color:white;font-weight:bold;'>{header}</div>"
                        value_html = f"<div style='background-color:#C0C0C0;padding:6px;border:1px solid black;font-weight:bold;color:black;'>{value}</div>"

                    cols[j * 2].markdown(header_html, unsafe_allow_html=True)
                    cols[j * 2 + 1].markdown(value_html, unsafe_allow_html=True)
            row += 1

        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⬅ Previous Record", use_container_width=True):
                jump_to_previous_unprocessed()
                st.rerun()

        with col2:
            if st.button("✅ Mark as Done", use_container_width=True):
                cons_no = str(record.get("CONS_NO", f"Row{st.session_state.current_index+1}"))
                st.session_state.done_records.add(cons_no)
                if cons_no in st.session_state.skipped_records:
                    st.session_state.skipped_records.remove(cons_no)
                save_log_to_memory(cons_no, "DONE")
                st.session_state.current_index += 1
                jump_to_next_unprocessed()
                st.rerun()

        with col3:
            skip_reason = st.text_input("Reason (for Skip):", key=f"skip_reason_{st.session_state.current_index}")
            if st.button("⏭ Skip Record", use_container_width=True):
                cons_no = str(record.get("CONS_NO", f"Row{st.session_state.current_index+1}"))
                if not skip_reason.strip():
                    st.warning("⚠️ Please enter a skip reason first!")
                else:
                    st.session_state.skipped_records.add(cons_no)
                    if cons_no in st.session_state.done_records:
                        st.session_state.done_records.remove(cons_no)
                    save_log_to_memory(cons_no, "SKIPPED", skip_reason)
                    st.session_state.current_index += 1
                    jump_to_next_unprocessed()
                    st.rerun()

        st.markdown("---")
        csv_data = pd.DataFrame(st.session_state.log_data).to_csv(index=False)
        st.download_button(
            "💾 Download Current Progress (Log File)",
            data=csv_data,
            file_name=f"{uploaded_excel.name}_progress_log.csv",
            mime="text/csv"
        )
