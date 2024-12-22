from typing import Literal
from fasthtml.common import *
from dataclasses import dataclass

@dataclass
class HighlightSettings:
    """
    es_highlight_token (str):
        Special token used in elasticsearch highlight, which the search fields are converted simplified chinese fields.
        Used to split and identify the offset of found keyword in original text
    start_token (str):
        Actual token used in original text display highlight, should be a start tag e.g. <em>
    end_token (str):
        Actual token used in original text display highlight, should be a end tag e.g. </em>
    """
    es_highlight_token: str
    start_token: str
    end_token: str

@dataclass
class Article:
    id: str
    publisher: str
    publish_location: str
    publish_date: str
    author_name: str
    title: str
    full_text: str

    @staticmethod
    def get_highlighted_text(original_text: str, highlighted_simplified_text: list[str]|None, highlight_settings: HighlightSettings) -> str:
        """highlight the original text using the highlighted simplified text as reference

        TODO:
            Add a max fragment length, any text in between the queried texts exceeding the limit should be replaced with "..."

        Args:
            original_text (str):
                The original text, could be either traditional chinese or simplified chinese
            highlighted_simplified_text (list[str] | None):
                Elasticsearch highlighted simplified text
                Make sure highlight.number_of_fragments is set to 0 such that len(highlighted_simplified_text) == 1
            highlight_settings (HighlightSettings):
                Variables used in the highlighting process

        Returns:
            str: highlighted original text
        """
        if highlighted_simplified_text is None:
            return original_text

        splitted_simplified_text = highlighted_simplified_text[0].split(highlight_settings.es_highlight_token)

        switch = [highlight_settings.end_token, highlight_settings.start_token]
        pos = 0

        output_constructor: list[str] = []
        for i, simplified_text in enumerate(splitted_simplified_text):
            text_len = len(simplified_text)
            if i == 0: # first fragment
                pass
            else:
                output_constructor.append(switch[i%2])
            output_constructor.append(original_text[pos:pos+text_len])

            pos += text_len

        return "".join(output_constructor)

    @classmethod
    def from_elastic_search_response(cls, es_query_res: dict[Literal["_source", "highlight"], Any], highlight_settings: HighlightSettings):
        return cls(
            id=es_query_res["_source"]["id"],
            publisher=Article.get_highlighted_text(es_query_res["_source"]["publisher"], es_query_res["highlight"].get("publisher_simplified"), highlight_settings),
            publish_location=Article.get_highlighted_text(es_query_res["_source"]["publish_location"], es_query_res["highlight"].get("publish_location_simplified"), highlight_settings),
            publish_date=es_query_res["_source"]["publish_date"],
            author_name=Article.get_highlighted_text(es_query_res["_source"]["author_name"], es_query_res["highlight"].get("author_name_simplified"), highlight_settings),
            title=Article.get_highlighted_text(es_query_res["_source"]["title"], es_query_res["highlight"].get("title_simplified"), highlight_settings),
            full_text=Article.get_highlighted_text(es_query_res["_source"]["full_text"], es_query_res["highlight"].get("full_text_simplified"), highlight_settings),
        )

    def __ft__(self):
        """The __ft__ method renders the dataclass at runtime."""
        return Div(
            Ul(
                Li(P(f"ID: {self.id}")),
                Li(P(f"Publisher: {self.publisher}")),
                Li(P(f"Publish Location: {self.publish_location}")),
                Li(P(f"Publish Date: {self.publish_date}")),
                Li(P(f"Author Name: {self.author_name}")),
                Li(P(f"Title: {self.title}")),
                Li(P(f"Full Text: {self.full_text}")),
            )
        )

class ArticleRow(Article):
    def __ft__(self):
        return Tr(
            Td(Safe(self.publisher)),
            Td(Safe(self.publish_location)),
            Td(self.publish_date, cls="text-nowrap"),
            Td(Safe(self.author_name)),
            Td(Safe(self.title)),
            Td(Safe(self.full_text)),
            Td(
                A("link", href="#", target="_blank"), # open the document in a new tab
                cls="text-blue-600"
            ),
            cls=[
                "text-center",
                "border-b",
                "border-8",
                "even:bg-blue-100",
                "odd:bg-amber-100",
                "hover:even:bg-blue-50",
                "hover:odd:bg-amber-50",
            ]
        )