import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Excel Data Viewer", layout="wide")

st.title("📘 Excel Data Viewer (Online)")
st.markdown("Upload Excel, review each record, and mark as ✅ Done or ⏭ Skip with reason.")
st.markdown("---")

if "data" not in st.session_state:
    st.session_state.data = None
    st.session_state.current_index = 0
    st.session_state.done_records = set()
    st.session_state.skipped_records = set()
    st.session_state.log_data = []


def save_log_to_memory(cons_no, action, reason=None):
    """Store log in session memory (export later)"""
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


uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, dtype=str).fillna("")
    st.session_state.data = df

    jump_to_next_unprocessed()
    df = st.session_state.data
    total = len(df)
    done = len(st.session_state.done_records)
    skipped = len(st.session_state.skipped_records)

    st.markdown(f"### Summary: Total {total} | ✅ Done {done} | ⏭ Skipped {skipped}")
    st.markdown("---")

    if st.session_state.current_index >= len(df):
        st.success("🎉 Job Completed Successfully!")
        st.download_button(
            "📥 Download Log File",
            data=pd.DataFrame(st.session_state.log_data).to_csv(index=False),
            file_name=f"{uploaded_file.name}_log.csv",
            mime="text/csv"
        )
    else:
        record = df.iloc[st.session_state.current_index]
        st.subheader(f"🔹 Record {st.session_state.current_index + 1} / {len(df)}")

        headers = record.index.tolist()
        values = record.values.tolist()
        group_size = 5
        cols = st.columns(group_size * 2)

        for i in range(0, len(headers), group_size):
            for j in range(group_size):
                if i + j < len(headers):
                    cols[j * 2].markdown(f"**{headers[i + j]}**")
                    cols[j * 2 + 1].markdown(f"<span style='font-weight:bold;color:black;'>{values[i + j]}</span>", unsafe_allow_html=True)

        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⬅ Previous Record", use_container_width=True):
                if st.session_state.current_index > 0:
                    st.session_state.current_index -= 1
                    st.rerun()
        with col2:
            if st.button("✅ Mark as Done", use_container_width=True):
                cons_no = str(record.get("CONS_NO", f"Row{st.session_state.current_index+1}"))
                st.session_state.done_records.add(cons_no)
                if cons_no in st.session_state.skipped_records:
                    st.session_state.skipped_records.remove(cons_no)
                save_log_to_memory(cons_no, "DONE")
                st.session_state.current_index += 1
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
                    st.rerun()
