from email import errors
from pydoc import text
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
    segment_max_length (int):
        Max length of text fragments displayed before/after detected keywords, text fragments longer than this will be trimmed
    segment_token (str):
        Token used to separate text fragments exceeding segment_max_length, could include html tag such as <br>
    """
    es_highlight_token: str
    start_token: str
    end_token: str
    segment_max_length: int
    segment_token: str

def _process_start_text(text_fragment: str, max_len: int, separator: str)->str:
    if len(text_fragment) < max_len:
        return text_fragment
    trimmed_text = "".join([separator, text_fragment[-max_len:]])
    return trimmed_text

def _process_end_text(text_fragment: str, max_len: int, separator: str)->str:
    if len(text_fragment) < max_len:
        return text_fragment
    trimmed_text = "".join([text_fragment[:max_len], separator])
    return trimmed_text

def _process_middle_text(text_fragment: str, max_len: int, separator: str)->str:
    if len(text_fragment) < max_len*2: # end of first keyword and start of next keyword
        return text_fragment
    trimmed_text = "".join([
        text_fragment[:max_len],
        separator,
        text_fragment[-max_len:],
    ])
    return trimmed_text


def _get_highlighted_text(original_text: str, highlighted_simplified_text: list[str]|None, highlight_settings: HighlightSettings) -> str:
    """highlight the original text using the highlighted simplified text as reference

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
        is_keyword = i%2
        if i > 0:
            output_constructor.append(switch[is_keyword])

        if is_start_text := i == 0:
            output_constructor.append(
                _process_start_text(
                    original_text[pos:pos+text_len],
                    highlight_settings.segment_max_length,
                    highlight_settings.segment_token,
                )
            )
        elif is_end_text := i == len(splitted_simplified_text)-1:
            output_constructor.append(
                _process_end_text(
                    original_text[pos:pos+text_len],
                    highlight_settings.segment_max_length,
                    highlight_settings.segment_token,
                )
            )
        else:
            output_constructor.append(
                _process_middle_text(
                    original_text[pos:pos+text_len],
                    highlight_settings.segment_max_length,
                    highlight_settings.segment_token,
                )
            )

        pos += text_len

    return "".join(output_constructor)

TEXT_FIELDS = ["publisher", "publish_location", "author_name", "title", "full_text"]
TEXT_FIELD_INVALID_MSG = "no consecutive '&', '|'"
DATE_FIELD_INVALID_MSG = "Accepted date format: YYYY, YYYYMM, YYYY-YYYY, YYYYMM-YYYYMM"

@dataclass
class ArticleSearchQuery:
    publisher: str
    publish_location: str
    publish_date: str
    author_name: str
    title: str
    full_text: str

    def non_empty(self)->bool:
        return any([self.publisher, self.publish_location, self.publish_date, self.author_name, self.title, self.full_text])

    def get_errors(self)->dict[str, str]:
        """Check if query is valid, return error messages if not valid.
        Query is valid if there are no consecutive &|, parsing brackets is complicated
        And the date format is correct
        """
        # TODO: support brackets
        invalid_pattern = "|".join([
            r"([&|]{2,})", # check if there are consecutive symbols
            r"^[&|]", # start with operator
            r"[&|]$", # end with operator
        ])
        errors = {}
        for name in TEXT_FIELDS:
            if re.search(invalid_pattern, getattr(self, name)):
                errors[name] = TEXT_FIELD_INVALID_MSG

        valid_date_patterns = "|".join([
            r"^(\d{4})$",
            r"^(\d{6})$",
            r"^(\d{4}-\d{4})$",
            r"^(\d{6}-\d{6})$",
        ])
        if self.publish_date and not re.search(valid_date_patterns, self.publish_date): # if not empty and not match the patterns
            errors["publish_date"] = DATE_FIELD_INVALID_MSG

        return errors
        # bracket_count = 0
        # for char in query:
        #     if char == "(":
        #         bracket_count += 1
        #     elif char == ")":
        #         bracket_count -= 1
        #     if bracket_count > 1:
        #         return False
        # return bracket_count == 0

    def parse_date(self)->tuple[str, str]:
        """Parse publish_date into start and end. Accepted format:
        1. YYYY
        2. YYYYMM
        3. YYYY-YYYY
        4. YYYYMM-YYYYMM
        """
        date_len = len(self.publish_date)
        def _next_month(year: str, month: str):
            if month != "12":
                return f"{year}-{int(month)+1:02}-01"
            return f"{int(year)+1}-01-01"

        if date_len == 4:
            return f"{self.publish_date}-01-01", f"{self.publish_date}-12-31"
        elif date_len == 6:
            year, month = self.publish_date[:4], self.publish_date[4:]
            return f"{year}-{month}-01", _next_month(year, month)
        elif date_len == 4+1+4:
            start_year, end_year = self.publish_date.split("-")
            return f"{start_year}-01-01", f"{end_year}-12-31"
        else: # 6+1+6
            start, end = self.publish_date.split("-")
            start_year, start_month = start[:4], start[4:]
            end_year, end_month = end[:4], end[4:]
            return f"{start_year}-{start_month}-01", _next_month(end_year, end_month)

    def __ft__(self):
        return Table(
            Tbody(*[
                Tr(
                    Td(field.replace("_", " ").title()),
                    Td(val or '-')
                ) for field, val in self.__dict__.items()
            ])
        )

@dataclass
class Article:
    id: str
    publisher: str
    publish_location: str
    publish_date: str
    author_name: str
    title: str
    full_text: str

    @classmethod
    def from_elastic_search_response(cls, es_query_res: dict[Literal["_source", "highlight"], Any], highlight_settings: HighlightSettings):
        if "highlight" not in es_query_res:
            es_query_res["highlight"] = {}
        if highlighted_full_text := es_query_res["highlight"].get("full_text_simplified"):
            displayed_full_text = _get_highlighted_text(es_query_res["_source"]["full_text"], highlighted_full_text, highlight_settings)
        else:
            displayed_full_text = "Full text too long to be displayed, please provide search for a keyword in full text"
        return cls(
            id=es_query_res["_source"]["id"],
            publisher=_get_highlighted_text(es_query_res["_source"]["publisher"], es_query_res["highlight"].get("publisher_simplified"), highlight_settings),
            publish_location=_get_highlighted_text(es_query_res["_source"]["publish_location"], es_query_res["highlight"].get("publish_location_simplified"), highlight_settings),
            publish_date=es_query_res["_source"]["publish_date"],
            author_name=_get_highlighted_text(es_query_res["_source"]["author_name"], es_query_res["highlight"].get("author_name_simplified"), highlight_settings),
            title=_get_highlighted_text(es_query_res["_source"]["title"], es_query_res["highlight"].get("title_simplified"), highlight_settings),
            full_text=displayed_full_text,
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