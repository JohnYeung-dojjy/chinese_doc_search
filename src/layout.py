from fasthtml.common import *

def base_layout(*args, **kwargs):
    return Body(
        Nav(H1("Chinese Doc Search")),
        Div(*args, **kwargs),
        cls=[
            "bg-gray-200",
        ]
    )