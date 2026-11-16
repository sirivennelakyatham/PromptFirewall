import streamlit as st
from datetime import datetime

from backend import process_prompt


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PromptFirewall",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# SHARED IN-MEMORY SECURITY LOG
# ============================================================

@st.cache_resource
def get_logs():
    return []


logs = get_logs()


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def admin_login():
    st.sidebar.markdown("## 🔐 Admin")

    password = st.sidebar.text_input(
        "Admin password",
        type="password"
    )

    if st.sidebar.button("Open Security Dashboard"):
        if password == st.secrets["ADMIN_PASSWORD"]:
            st.session_state.admin_authenticated = True
        else:
            st.sidebar.error("Incorrect password.")

    if st.session_state.get("admin_authenticated", False):
        if st.sidebar.button("Logout"):
            st.session_state.admin_authenticated = False
            st.rerun()


# ============================================================
# INITIALIZE USER CHAT
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

admin_login()

st.sidebar.markdown("---")
st.sidebar.caption(
    "PromptFirewall protects the LLM using a "
    "TF-IDF + Logistic Regression detector."
)


# ============================================================
# MAIN USER INTERFACE
# ============================================================

st.title("🛡️ PromptFirewall")

st.caption(
    "AI assistant protected by a prompt injection and jailbreak detector."
)


# Display previous conversation
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# USER INPUT
# ============================================================

prompt = st.chat_input("Ask the AI assistant something...")


if prompt:

    # --------------------------------------------------------
    # Display user's message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)


    # --------------------------------------------------------
    # Run security + LLM pipeline
    # --------------------------------------------------------

    with st.spinner("Checking your prompt..."):

        result = process_prompt(prompt)


    # --------------------------------------------------------
    # Save security log
    # --------------------------------------------------------

    logs.append(
        {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "prompt": prompt,
            "label": result["label"],
            "malicious_probability": result[
                "malicious_probability"
            ],
            "confidence": result["confidence"],
            "rule_flags": result["rule_flags"],
            "blocked": result["blocked"],
        }
    )


    # --------------------------------------------------------
    # MALICIOUS PROMPT
    # --------------------------------------------------------

    if result["blocked"]:

        reply = (
            "🚫 **This prompt was detected as unsafe "
            "and was blocked.**\n\n"
            "The prompt was not sent to the language model."
        )

        with st.chat_message("assistant"):
            st.error(reply)


    # --------------------------------------------------------
    # BENIGN PROMPT
    # --------------------------------------------------------

    else:

        if result["llm_response"]:

            reply = result["llm_response"]

            with st.chat_message("assistant"):
                st.markdown(reply)

        else:

            reply = (
                "⚠️ The prompt passed the security check, "
                "but the language model could not be reached."
            )

            with st.chat_message("assistant"):
                st.warning(reply)


    # Save assistant response to chat history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply
        }
    )


# ============================================================
# ADMIN SECURITY DASHBOARD
# ============================================================

if st.session_state.get("admin_authenticated", False):

    st.divider()

    st.header("🔎 Security Dashboard")

    st.caption(
        "Administrator view — security information is hidden "
        "from normal users."
    )


    if not logs:

        st.info("No prompts have been processed yet.")

    else:

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        total = len(logs)

        blocked = sum(
            1 for entry in logs
            if entry["blocked"]
        )

        allowed = total - blocked

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Prompts",
            total
        )

        col2.metric(
            "Allowed",
            allowed
        )

        col3.metric(
            "Blocked",
            blocked
        )


        st.divider()


        # ----------------------------------------------------
        # Individual security events
        # ----------------------------------------------------

        for i, entry in enumerate(reversed(logs), 1):

            status = (
                "🚫 BLOCKED"
                if entry["blocked"]
                else "✅ ALLOWED"
            )

            with st.expander(
                f"{status} — {entry['timestamp']}"
            ):

                st.markdown("### Prompt")

                st.code(
                    entry["prompt"],
                    language=None
                )


                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "ML Prediction",
                        entry["label"].upper()
                    )

                    st.metric(
                        "Malicious Probability",
                        f"{entry['malicious_probability']:.4f}"
                    )


                with col2:

                    st.metric(
                        "Confidence",
                        f"{entry['confidence']:.4f}"
                    )

                    st.metric(
                        "LLM Request",
                        "BLOCKED"
                        if entry["blocked"]
                        else "SENT"
                    )


                st.markdown("### Attack Indicators")

                if entry["rule_flags"]:

                    for flag in entry["rule_flags"]:
                        st.warning(f"⚠️ {flag}")

                else:

                    st.success(
                        "No rule-based attack indicators detected."
                    )


        # ----------------------------------------------------
        # Clear logs
        # ----------------------------------------------------

        st.divider()

        if st.button("🗑️ Clear Security Logs"):

            logs.clear()

            st.success("Security logs cleared.")

            st.rerun()