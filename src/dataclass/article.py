from fasthtml.common import *
from dataclasses import dataclass

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
    def from_elastic_search_response(cls, response: dict):
        return cls(
            id=response["id"],
            publisher=response["publisher"],
            publish_location=response["publish_location"],
            publish_date=response["publish_date"],
            author_name=response["author_name"],
            title=response["title"],
            full_text=response["full_text"],
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
            Td(self.publisher),
            Td(self.publish_location),
            Td(self.publish_date, cls="text-nowrap"),
            Td(self.author_name),
            Td(self.title),
            Td(self.full_text),
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