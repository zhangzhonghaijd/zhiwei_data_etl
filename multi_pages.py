import streamlit as st


class MultiPages:
    def __init__(self):
        self.apps = []
        self.app_dicts = {}

    def add_app(self, title, func):
        if title not in self.apps:
            self.apps.append(title)
            self.app_dicts[title] = func

    def run(self):
        title = st.sidebar.radio(
            label = '',
            options = self.apps,
            format_func = lambda title: str(title),
            horizontal=False,
        )
        self.app_dicts[title]()