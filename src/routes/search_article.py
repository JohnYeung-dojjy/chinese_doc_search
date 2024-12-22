from typing import Literal
from fasthtml.common import *
from layout import base_layout
from database import es
from dataclass.article import ArticleRow, HighlightSettings
from functools import partial
import chinese_converter

# Special string used in elasticsearch highlight
# used to split the highlighted simplified text and
# get the correct offset to add the highlight in original text
HIGHLIGHT_SETTINGS = HighlightSettings(
    es_highlight_token="~!~",
    start_token="<mark>",
    end_token="</mark>",
    segment_max_length=20,
    segment_token=" <b>...</b> "
)

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
            SearchLabel("Publish Date Start", SearchInput(type="date", name="publish_date_start", placeholder="YYYY-MM-DD")),
            SearchLabel("Publish Date End", SearchInput(type="date", name="publish_date_end", placeholder="YYYY-MM-DD")),
        ),
        Div(
            SearchLabel("Author Name", SearchInput(type="text", name="author_name")),
            SearchLabel("Title", SearchInput(type="text", name="title")),
            SearchLabel("Full Text", SearchInput(type="text", name="full_text")),
        ),
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

def _build_elastic_search_query(
    publisher: str,
    publish_location: str,
    publish_date_start: str,
    publish_date_end: str,
    author_name: str,
    title: str,
    full_text: str,
)->list[dict[str, dict[str, str|dict[str, str]]]]:
    compound_queries = []
    if publish_date_start and publish_date_end:
        query = {"range": {"publish_date": {"gte": publish_date_start, "lte": publish_date_end}}}
        compound_queries.append(query)
    if publisher:
        query = {"match_phrase": {"publisher_simplified": chinese_converter.t2s.convert(publisher)}}
        compound_queries.append(query)
    if publish_location:
        query = {"match_phrase": {"publish_location_simplified": chinese_converter.t2s.convert(publish_location)}}
        compound_queries.append(query)
    if author_name:
        query = {"match_phrase": {"author_name_simplified": chinese_converter.t2s.convert(author_name)}}
        compound_queries.append(query)
    if title:
        query = {"match_phrase": {"title_simplified": chinese_converter.t2s.convert(title)}}
        compound_queries.append(query)
    if full_text:
        query = {"match_phrase": {"full_text_simplified": chinese_converter.t2s.convert(full_text)}}
        compound_queries.append(query)
    return compound_queries

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
    """Search article documents in elasticsearch with the given keywords"""
    es_search_body = {
        "query": {
            "bool": {
                "must": _build_elastic_search_query(
                    publisher,
                    publish_location,
                    publish_date_start,
                    publish_date_end,
                    author_name,
                    title,
                    full_text,
                ),
            },
        },
        "highlight" : {
            "pre_tags" : [HIGHLIGHT_SETTINGS.es_highlight_token],
            "post_tags" : [HIGHLIGHT_SETTINGS.es_highlight_token],
            # get the highlighted full text, so we can somehow extract the offsets and cast the highlight to the original text
            # We should not display the simplified text to user due to library practices
            "number_of_fragments": 0,
            "fields" : {
                "publisher_simplified" : {},
                "publish_location_simplified": {},
                "author_name_simplified": {},
                "title_simplified": {},
                "full_text_simplified": {},
            }
        },
        "size": per_page,
        "from": page_id*per_page,
        "sort": {"publish_date": {"order": "desc"}},
    }

    response = es.search(
        index=os.environ["ELASTICSEARCH_INDEX"],
        body=es_search_body,
    )

    queried_documents: list[dict[Literal["_source", "highlight"], Any]] = response["hits"]["hits"]

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
            *(ArticleRow.from_elastic_search_response(doc, HIGHLIGHT_SETTINGS) for doc in queried_documents),
        ),
        cls=[
            "table-auto",
            "w-11/12",
            "border-8",
            "text-l",
        ]
    )