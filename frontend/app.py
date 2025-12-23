#streamlit entry point

import streamlit as st
from api import shorten_url, get_all_urls, get_stats,get_trending

st.set_page_config(page_title="URL Shortener", layout="centered")

st.title("URL Shortener")

tabs = st.tabs(["Shorten URL", "Stats", "Admin"])

#tab 1 - shorten url
with tabs[0]:
    st.subheader("Shorten a URL")

    long_url = st.text_input("Enter long URL")

    if st.button("Shorten"):
        if not long_url:
            st.error("Please enter a URL")
        else:
            res = shorten_url(long_url)
            if res.status_code == 200:
                short_url = res.json()["short_url"]
                st.success("Short URL created!")
                st.code(short_url)
                st.markdown(f"[🔗 Open link]({short_url})")
            else:
                st.error(res.text)

#tab 2 - stats
with tabs[1]:
    st.subheader("URL Stats")

    short_code = st.text_input("Enter short code (example- Ab12Xy)")

    if st.button("Get Stats"):
        if not short_code:
            st.error("Enter short code")
        else:
            res = get_stats(short_code)
            if res.status_code == 200:
                data = res.json()
                st.json(data)
            else:
                st.error(res.text)

#tab 3 - admin
with tabs[2]:
    st.subheader("Admin Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("All URLs"):
            res = get_all_urls()
            if res.status_code == 200:
                st.table(res.json()["urls"])
    

    with col2:
        if st.button("Trending URLs"):
            res = get_trending()
            if res.status_code== 200:
                st.table(res.json()["urls"])