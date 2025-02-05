import streamlit as st
import pyautogui

def reset_session_state_and_rerun(exclude_keys=None):
    if exclude_keys is None:
        exclude_keys = []
    for key in list(st.session_state.keys()):
        if key not in exclude_keys:
            del st.session_state[key]
    pyautogui.hotkey("ctrl","F5")
    #st.rerun(scope="app")