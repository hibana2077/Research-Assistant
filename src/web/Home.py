import streamlit as st
import os
import requests

# Self-defined imports
from utils.auth import login, register

if 'login' not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    # 建立 Login 與 Register 兩個 tabs
    tabs = st.tabs(["Login", "Register"])
    
    with tabs[0]:
        # Login 表單
        with st.form(key='login_form'):
            st.title('Login')
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            submit_button = st.form_submit_button(label='Login')
            if submit_button:
                login_result = login(username, password)
                if login_result:
                    st.session_state.login = login_result
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your username and password.")
    
    with tabs[1]:
        # Register 表單
        with st.form(key='register_form'):
            st.title('Register')
            new_username = st.text_input('New Username')
            new_password = st.text_input('New Password', type='password')
            confirm_password = st.text_input('Confirm Password', type='password')
            register_button = st.form_submit_button(label='Register')
            if register_button:
                if new_password != confirm_password:
                    st.error("Password and Confirm Password do not match.")
                else:
                    register_result = register(new_username, new_password)
                    if register_result:
                        st.success("Registration successful! You can now log in.")
                    else:
                        st.error("Registration failed. Please try again.")
else:
    # 主頁內容
    st.title("🔬 Lab")
    st.divider()
    
    col_l, col_r = st.columns([3, 1])