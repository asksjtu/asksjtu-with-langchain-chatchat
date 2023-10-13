import streamlit as st
import streamlit.components.v1 as components


def hide_main_menu_and_footer():
    return """
    <style>
    #MainMenu {display: none;}
    footer {display: none;}
    </style>
    """


def hide_padding_making_with_strealit():
    return """
    <style>
    @media (max-width: 768px) {
        .stChatFloatingInputContainer {padding-bottom: 2rem !important;}
    }
    </style>
    """


def hide_cookie_manager_containers():
    return """
    <style>
    .element-container:has(iframe[title="extra_streamlit_components.CookieManager.cookie_manager"]) {
        display: none;
    }
    iframe[title="extra_streamlit_components.CookieManager.cookie_manager"] {
        display: none;
    }
    </style>
    """ 


def style_hack():
    # dialogue page
    tweaks = ""
    tweaks += hide_main_menu_and_footer()
    tweaks += hide_padding_making_with_strealit()
    tweaks += hide_cookie_manager_containers()
    st.markdown(tweaks, unsafe_allow_html=True) 
