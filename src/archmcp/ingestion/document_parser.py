"""
Parser for Markdown documentation, architecture notes, and READMEs.

@author Shubham Upadhyay
@license MIT
"""

from ..models.document import Document


class DocumentParser:
    """
    Extracts sections, headings, and structured metadata from documentation.
    """

    @staticmethod
    def parse_markdown(service_id: str, title: str, content: str, tenant_id: str = "default") -> Document:
        """
        Parses raw markdown text into a structured Document model.

        @param str service_id: Unique microservice identifier
        @param str title: Document title
        @param str content: Raw markdown text content
        @param str tenant_id: Multi-tenant boundary identifier
        @return Document: Structured Document entity
        """
        lines = content.splitlines()
        tags = []
        for line in lines:
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                if heading:
                    tags.append(heading.lower())

        doc_id = f"doc_{service_id}_{title.lower().replace(' ', '_')}"
        return Document(
            id=doc_id,
            title=title,
            service_id=service_id,
            content=content,
            tenant_id=tenant_id
        )

