import os
from dotenv import load_dotenv
from fasthtml.common import *

from routes import (
    entry,
    display_table,
    search_article,
)


load_dotenv()

debug = os.environ["DEBUG"].upper() == "TRUE"
app = FastHTML(
    title="Chinese Doc Search",
    debug=debug,
    pico=False, # disable pico css, only use Tailwind
    hdrs=(
        # JQuery
        Script(
            src="https://code.jquery.com/jquery-3.7.1.slim.min.js",
            integrity="sha256-kmHvs0B+OpCW5GVHUNjv9rOmY0IvSIRcf7zGUDTDQM8=",
            crossorigin="anonymous"
        ),

        # Select2
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css"),
        Script(src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"),

        # Tailwind
        Script(src="https://cdn.tailwindcss.com")
    )
)

app.get("/")(entry.home)
app.get("/display")(display_table.display_table)
app.get("/search-article-page")(search_article.article_search_page)
app.post("/search-article")(search_article.search_article)

serve()
