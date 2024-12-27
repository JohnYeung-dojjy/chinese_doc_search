from typing import Literal
from fasthtml.common import *
from layout import base_layout
from database import es
from dataclass.article import ArticleRow, HighlightSettings
from functools import partial
import chinese_converter
import re

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

PER_PAGE_OPTIONS = [10, 20, 50]

BTN_ACTIVATED_CLS = "bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
BTN_DEACTIVATED_CLS = "bg-blue-200 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"

FORM_SUBMISSION_HTMX_KW = dict(
    method="post",
    hx_post="/search-article",
    hx_vals=r"js:{per_page: perPage, page_id: pageNum}",
    hx_target="#search_result_table",
    hx_swap="innerHTML",
)

DEFAULT_DISPLAY_ROWS: int = 10

PAGINATION_SETTING_JS = """
    let perPage = 10;
    let pageNum = 0;

    /* Must use function(){} else $(this) is the same as outer scope */
    $("[id^=id_per_page-]").on("click", function() {
        /* Get the first page of the updated query */
        let shouldUpdatePage = $(this).val() !== perPage;
        if (!shouldUpdatePage) { return; }

        perPage = $(this).val();
        pageNum = 0;

        /* Update btn ui */
        $("[id^=id_per_page-]").each(function() {
            if ($(this).val() === perPage) {
                $(this).removeClass("bg-blue-200").addClass("bg-blue-500");
            } else {
                $(this).removeClass("bg-blue-500").addClass("bg-blue-200");
            }
        })

        /* Resubmit the form */
        $("#search_result_table").submit();
    })
"""

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
    id="article_search_form",
    onclick="perNum=0",
    **FORM_SUBMISSION_HTMX_KW,
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
        Div(
            Label(
                "Display Rows",
                cls=[
                    "mb-2",
                    "text-sm",
                    "font-medium",
                    "text-gray-900",
                    "p-2",
                ]
            ),
            Span(
                *[Button(
                        val,
                        type="submit",
                        id=f"id_per_page-{val}",
                        value=val,
                        cls=BTN_ACTIVATED_CLS if val == DEFAULT_DISPLAY_ROWS else BTN_DEACTIVATED_CLS
                    ) for val in PER_PAGE_OPTIONS],
                Script(PAGINATION_SETTING_JS),
            ),
            cls=[
                # "flex",
            ]
        ),
        Button("Search", type="submit",
            cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded",
        ),
        cls="flex justify-between"
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

def _is_query_valid(query: str) -> bool:
    """Query is valid if there are no consecutive &|, parsing brackets is complicated"""
    # TODO: support brackets
    invalid_pattern = "|".join([
        r"([&|]{2,})", # check if there are consecutive symbols
    ])
    if re.search(invalid_pattern, query):
        return False
    return True
    # bracket_count = 0
    # for char in query:
    #     if char == "(":
    #         bracket_count += 1
    #     elif char == ")":
    #         bracket_count -= 1
    #     if bracket_count > 1:
    #         return False
    # return bracket_count == 0

def _parse_query(query: str, target_field: str):
    """Parse user input query (containing `&`, `|`) to elasticsearch query

    Args:
        query (str): User input query containing keywords
    """

    query = query.replace(" ", "")
    or_queries = query.split("|")
    and_queries = [subquery.split("&") for subquery in or_queries]

    es_query = {"bool": {"should": []}}

    for and_query in and_queries:
        if len(and_query) == 1:
            q = {"match_phrase": {target_field: and_query[0]}}
        else:
            q = {
                "bool": {
                    "must": [
                        {"match_phrase": {target_field: item}} for item in and_query
                    ]
                }
            }
        es_query["bool"]["should"].append(q)
    return es_query

def _build_elastic_search_query(
    publisher: str,
    publish_location: str,
    publish_date_start: str,
    publish_date_end: str,
    author_name: str,
    title: str,
    full_text: str,
)->list[dict[str, dict[str, str|dict[str, str]]]]:

    errors = {}
    local_variables = locals()
    for name in ["publisher", "publish_location", "author_name", "title", "full_text"]:
        if not _is_query_valid(local_variables[name]):
            errors[name] = "Invalid query, nested brackets or open/close brackets does not match, consecutive &| is not allowed"
    if errors:
        raise ValueError(errors)

    compound_queries = []
    if publish_date_start and publish_date_end:
        query = {"range": {"publish_date": {"gte": publish_date_start, "lte": publish_date_end}}}
        compound_queries.append(query)

    for name in ["publisher", "publish_location", "author_name", "title", "full_text"]:
        if value:=local_variables[name]:
            query = _parse_query(chinese_converter.t2s.convert(value), f"{name}_simplified")
            compound_queries.append(query)
    return compound_queries

ARTICLE_TABLE_HEAD = Thead(
    Tr(Th(name, scope="col") for name in ("Publisher", "Publish Location", "Publish Date", "Author Name", "Title", "Full Text", "Source File")),
    cls=[
        "text-s",
        "uppercase",
        "bg-gray-500",
    ]
)
ARTICLE_TABLE_CLS = cls=[
        "table-auto",
        "w-11/12",
        "border-8",
        "text-l",
    ]

# handles post request
def search_article(
    publisher: str,
    publish_location: str,
    publish_date_start: str,
    publish_date_end: str,
    author_name: str,
    title: str,
    full_text: str,
    per_page: int,
    page_id: int,
):
    """Search article documents in elasticsearch with the given keywords"""
    if not any([publisher, publish_location, publish_date_start, publish_date_end, author_name, title, full_text]):
        return Table(ARTICLE_TABLE_HEAD, cls=ARTICLE_TABLE_CLS)
    try:
        search_query = _build_elastic_search_query(
            publisher,
            publish_location,
            publish_date_start,
            publish_date_end,
            author_name,
            title,
            full_text,
        )
    except ValueError as e:
        #TODO: display error in form and remove content in table
        return Div(
            P(str(e)),
            cls=[
                "flex",
                "w-full",
                "justify-self-start",
                "border-8",
            ]
        )
    # Avoid hacker
    per_page = max(per_page, 1)
    page_id = max(page_id, 0)
    es_search_body = {
        "query": {
            "bool": {
                "must": search_query,
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

    total_pages = math.ceil(response['hits']['total']['value'] / per_page)
    curr_page = page_id + 1
    prev_page_btn = None if curr_page==1 else Button(
        "Previous", type="submit", id=f"page_{page_id-1}",
        onclick="pageNum-=1",
        hx_include="#article_search_form",
        **FORM_SUBMISSION_HTMX_KW, cls=BTN_ACTIVATED_CLS,
    )
    next_page_btn = None if curr_page==total_pages else Button(
        "Next", type="submit", id=f"page_{page_id+1}",
        onclick="pageNum+=1",
        hx_include="#article_search_form",
        **FORM_SUBMISSION_HTMX_KW, cls=BTN_ACTIVATED_CLS,
    )
    pagination = Div(
        Div(prev_page_btn),
        Span(f"Showing page {curr_page} of {total_pages}", cls="inline-block align-middle hover:align-top"),
        Div(next_page_btn),
        cls=[
            "flex",
            "justify-between",
            "px-8",
            "py-2",
        ]
    )

    return Div(
        pagination,
        Table(
            ARTICLE_TABLE_HEAD,
            Tbody(
                *(ArticleRow.from_elastic_search_response(doc, HIGHLIGHT_SETTINGS) for doc in queried_documents),
            ),
        ),
        pagination,
    )
