import streamlit as st


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
    </sytle>
    """

def style_hack():
    # dialogue page
    tweaks = ""
    tweaks += hide_main_menu_and_footer()
    tweaks += hide_padding_making_with_strealit()
    st.markdown(tweaks, unsafe_allow_html=True) 
