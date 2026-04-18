import streamlit as st
import json
import os
from datetime import datetime

# Page config
st.set_page_config(page_title="Nsight Agent Log Viewer", layout="wide")

st.title("🧠 Nsight Agent Node Execution Viewer")

LOG_FILE = "logs/agent_execution.jsonl"

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    logs = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        return logs
    except Exception as e:
        st.error(f"Error loading logs: {e}")
        return []

logs = load_logs()

if not logs:
    st.info("No logs found. Run the agent first!")
else:
    # Sidebar for filtering
    st.sidebar.header("Filters")
    node_options = ["All"] + list(set([log["node"] for log in logs]))
    selected_node = st.sidebar.selectbox("Select Node", node_options)
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Logs"):
        st.rerun()

    # Filter logs
    filtered_logs = logs
    if selected_node != "All":
        filtered_logs = [log for log in logs if log["node"] == selected_node]
    
    # Reverse to show latest first
    filtered_logs = filtered_logs[::-1]

    for i, log in enumerate(filtered_logs):
        with st.expander(f"[{log['timestamp']}] Node: {log['node']} | Status: {log['status']} | Duration: {log['duration_sec']}s", expanded=(i==0)):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📥 Input")
                input_data = log.get("input", {})
                if isinstance(input_data, dict):
                    for key, val in input_data.items():
                        if isinstance(val, str) and ("__global__" in val or "#include" in val):
                            st.text(f"Key: {key} (CUDA Code)")
                            st.code(val, language="cpp")
                        elif isinstance(val, str) and len(val) > 200:
                            st.text(f"Key: {key} (Long Text)")
                            st.markdown(val)
                        else:
                            st.json({key: val})
                else:
                    st.write(input_data)

            with col2:
                st.subheader("📤 Output / Error")
                if log["status"] == "success":
                    output_data = log.get("output", {})
                    if isinstance(output_data, dict):
                        for key, val in output_data.items():
                            if isinstance(val, str) and ("__global__" in val or "#include" in val):
                                st.text(f"Key: {key} (CUDA Code)")
                                st.code(val, language="cpp")
                            elif isinstance(val, str) and ("import torch" in val or "def " in val):
                                st.text(f"Key: {key} (Python Code)")
                                st.code(val, language="python")
                            elif isinstance(val, str) and len(val) > 200:
                                st.text(f"Key: {key} (Report/Summary)")
                                st.markdown(val)
                            else:
                                st.json({key: val})
                    else:
                        st.write(output_data)
                else:
                    st.error(f"Error: {log.get('error')}")

st.sidebar.markdown("---")
st.sidebar.caption("Nsight Agent Debugging Tool v1.0")
