from fasthtml.common import *
from layout import base_layout
from database import es
from dataclass.article import ArticleRow
from functools import partial

SearchLabel = partial(Label, cls=[
    # "block",
    "mb-2",
    "text-sm",
    "font-medium",
    "text-gray-900",
    "p-2",
    # "dark:text-white",
])
SearchInput = partial(Input, cls=[
    "bg-gray-50",
    "border",
    "border-gray-300",
    "text-gray-900",
    "text-sm",
    "rounded-lg",
    "focus:ring-blue-500",
    "focus:border-blue-500",
    # "block",
    # "w-full",
    "p-2.5",
    # "dark:bg-gray-700",
    # "dark:border-gray-600",
    # "dark:placeholder-gray-400",
    # "dark:text-white",
    # "dark:focus:ring-blue-500",
    # "dark:focus:border-blue-500",
])

article_search_form = Form(
    method="post",
    hx_post="/search-article",
    hx_target="#search_result_table",
    hx_swap="innerHTML",
)(
    Fieldset(
        Div(
            SearchLabel("Publisher", SearchInput(type="text", name="publisher")),
            SearchLabel("Publish Location", SearchInput(type="text", name="publish_location")),
        ),
        Div(
            SearchLabel("Publish Date Start", SearchInput(type="date", name="publish_date_start", placeholder="YYYY-MM-DD")),
            SearchLabel("Publish Date End", SearchInput(type="date", name="publish_date_end", placeholder="YYYY-MM-DD")),
        ),
        SearchLabel("Author Name", SearchInput(type="text", name="author_name")),
        SearchLabel("Title", SearchInput(type="text", name="title")),
        SearchLabel("Full Text", SearchInput(type="text", name="full_text")),
        cls=[
            "grid",
            "grid-cols-1",
        ]
    ),
    Div(
        Button("Search", type="submit",
            cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded",
        ),
        cls="justify-self-end"
    ),
    cls=[
        "justify-self-auto",
        "border-2",
        "p-2",
        "border-indigo-500/75",
        "rounded-lg",
    ]
)

# handles get request
def article_search_page():
    return base_layout(
        Div(
            article_search_form,
            cls=[
                "flex",
                "w-full",
                "justify-self-start",
                "border-8",
            ]
        ),
        Div(id="search_result_table",
            cls=[
                "w-full",
            ]
        )
    )

# handles post request
def search_article(
    publisher: str,
    publish_location: str,
    publish_date_start: str,
    publish_date_end: str,
    author_name: str,
    title: str,
    full_text: str,
    per_page: int = 10,
    page_id: int = 0,
):
    es_search_body = {
        "query": {
            "match_all": {}
        },
        "size": per_page,
        "from": page_id*per_page,
    }

    response = es.search(
        index=os.environ["ELASTICSEARCH_INDEX"],
        body=es_search_body,
    )
    result = [item["_source"] for item in response["hits"]["hits"]]

    return Table(
        Thead(
            Tr(Th(name, scope="col") for name in ("Publisher", "Publish Location", "Publish Date", "Author Name", "Title", "Full Text", "Source File")),
            cls=[
                "text-s",
                "uppercase",
                "bg-gray-500",
            ]
        ),
        Tbody(
            *(ArticleRow.from_elastic_search_response(item) for item in result),
        ),
        cls=[
            "table-auto",
            "w-11/12",
            "border-8",
            "text-l",
        ]
    )