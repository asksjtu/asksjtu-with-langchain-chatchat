from dataclasses import dataclass, asdict
from typing import List, Any
from streamlit_chatbox import OutputElement
import streamlit as st
import json
import uuid


@dataclass
class DownloadButtonProps:
    name: str
    path: str


class DownloadButtons(OutputElement):
    def __init__(
        self,
        content: DownloadButtonProps | List[DownloadButtonProps] = "",
        cols: int = 4,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Custom Chatbox Component for outputing download buttons.
        """
        self._cols = cols
        if isinstance(content, DownloadButtonProps):
            content = [content]
        _content = json.dumps([asdict(c) for c in content])
        super().__init__(
            _content, *args, **kwargs,
        )

    @property
    def real_content(self):
        c_json = json.loads(self._content)
        return [DownloadButtonProps(**c) for c in c_json]

    def output_method(self, links: List[DownloadButtonProps], render_to: st._DeltaGenerator):
        if render_to is None:
            render_to = st

        container = render_to.container()
        if len(links) == 0:
            return container

        col_cnt = min(self._cols, len(links))
        cols = container.columns(col_cnt)
        for link_id, link in enumerate(links):
            col_id = link_id % col_cnt
            with open(link.path, "rb") as file:
                cols[col_id].download_button(
                    f"下载 {link.name}",
                    data=file,
                    file_name=link.name,
                    key=uuid.uuid4(),
                    use_container_width=True,
                )
        return container

    def __call__(self, render_to: st._DeltaGenerator=None, direct: bool=False) -> st._DeltaGenerator:
        if render_to is None:
            if self._place_holder is None:
                self._place_holder = st.empty()
        else:
            if direct:
                self._place_holder = render_to
            else:
                self._place_holder = render_to.empty()

        self._dg = self.output_method(self.real_content, render_to=render_to)
        return self._dg

    def update_element(
        self,
        element: "OutputElement" = None,
        *,
        title: str = None,
        expanded: bool = None,
        state: bool = None,
    ) -> st._DeltaGenerator:
        assert self.place_holder is not None, f"You must render the element {self} before setting new element."
        attrs = {}
        if title is not None:
            attrs["_title"] = title
        if expanded is not None:
            attrs["_expanded"] = expanded
        if state is not None:
            attrs["_state"] = state

        if element is None:
            element = self
        for k, v in attrs.items():
            setattr(element, k, v)
        
        element(self.place_holder, direct=True)
        return self._dg

    def status_from(self, target):
        for attr in ["_in_expander", "_expanded", "_title", "_state"]:
            setattr(self, attr, getattr(target, attr))
