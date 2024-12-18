from fasthtml.common import *
from database import es
from dataclass.article import ArticleRow
from layout import base_layout

def display_table():
    """Returns a table of first 10 entries in the database"""

    response = es.search(
        index="fake_chinese_articles_collection_data",
        body={
            "query": {
                "match_all": {}
            },
            "size": 10,
            "from": 10,
        }
    )
    result = [item["_source"] for item in response["hits"]["hits"]]
    return base_layout(
        Table(
            Thead(
                Tr(Th(name, scope="col") for name in ("ID", "Publisher", "Publish Location", "Publish Date", "Author Name", "Title", "Full Text")),
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
                "text-l",
            ]
        )
    )
