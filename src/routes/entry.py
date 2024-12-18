from fasthtml.common import *
from layout import base_layout

def home():
    return base_layout("FastHTML", P("Let's do this!"))
