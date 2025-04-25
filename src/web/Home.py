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
    
    with col_l:
        st.write('Your paper idea:')
    with col_r:
        new_kb = st.button('New idea', key='new_kb')
        if new_kb:
            new_kb_dialog()
    
    kb_left, kb_mid, kb_right = st.columns(3)
    act_kb = list_all_knowledge_bases(st.session_state.username)
    if act_kb['count'] > 0:
        for it, kb in enumerate(act_kb['data']):
            where = kb_left if it % 3 == 0 else kb_mid if it % 3 == 1 else kb_right
            new_container = where.container(key=f'kb_{it}', border=True)
            with new_container:
                st.markdown(f"## {kb['icon']} {kb['name']}")
                st.write(kb['desc'])
                if st.button('Open', key=f'open_kb_{it}'):
                    view_kb_dialog(kb['name'])