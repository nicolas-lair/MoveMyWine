import hmac

import streamlit as st


def check_password() -> bool:
    """Return True once the user has entered the shared password (stored in st.secrets)."""
    if st.session_state.get("password_correct", False):
        return True

    def password_entered():
        st.session_state["password_correct"] = hmac.compare_digest(
            st.session_state["password"], st.secrets["password"]
        )
        # Do not keep the password in session state
        del st.session_state["password"]

    st.text_input(
        "Mot de passe", type="password", on_change=password_entered, key="password"
    )
    if st.session_state.get("password_correct") is False:
        st.error("Mot de passe incorrect")
    return False
