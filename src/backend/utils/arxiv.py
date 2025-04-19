import urllib.request
from urllib.parse import urlparse
from typing import List, Dict, Optional, Any
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import fromstring


class ArXivComponent:
    """
    A component to search and retrieve papers from arXiv.org
    """
    
    def __init__(
        self, 
        search_query: str,
        search_type: str = "all",
        max_results: int = 10
    ):
        """
        Initialize the ArXiv component.
        
        Args:
            search_query: The search query for arXiv papers (e.g., 'quantum computing')
            search_type: Field to search in ("all", "title", "abstract", "author", "cat")
            max_results: Maximum number of results to return
        """
        self.search_query = search_query
        self.search_type = search_type
        self.max_results = max_results
        self.status = None

    def build_query_url(self) -> str:
        """Build the arXiv API query URL."""
        base_url = "http://export.arxiv.org/api/query?"

        # Build the search query
        search_query = f"{self.search_type}:{self.search_query}"

        # URL parameters
        params = {
            "search_query": search_query,
            "max_results": str(self.max_results),
        }

        # Convert params to URL query string
        query_string = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])

        return base_url + query_string

    def parse_atom_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the Atom XML response from arXiv."""
        # Parse XML safely using defusedxml
        root = fromstring(response_text)

        # Define namespace dictionary for XML parsing
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        papers = []
        # Process each entry (paper)
        for entry in root.findall("atom:entry", ns):
            paper = {
                "id": self._get_text(entry, "atom:id", ns),
                "title": self._get_text(entry, "atom:title", ns),
                "summary": self._get_text(entry, "atom:summary", ns),
                "published": self._get_text(entry, "atom:published", ns),
                "updated": self._get_text(entry, "atom:updated", ns),
                "authors": [author.find("atom:name", ns).text for author in entry.findall("atom:author", ns)],
                "arxiv_url": self._get_link(entry, "alternate", ns),
                "pdf_url": self._get_link(entry, "related", ns),
                "comment": self._get_text(entry, "arxiv:comment", ns),
                "journal_ref": self._get_text(entry, "arxiv:journal_ref", ns),
                "primary_category": self._get_category(entry, ns),
                "categories": [cat.get("term") for cat in entry.findall("atom:category", ns)],
            }
            papers.append(paper)

        return papers

    def _get_text(self, element: Element, path: str, ns: dict) -> Optional[str]:
        """Safely extract text from an XML element."""
        el = element.find(path, ns)
        return el.text.strip() if el is not None and el.text else None

    def _get_link(self, element: Element, rel: str, ns: dict) -> Optional[str]:
        """Get link URL based on relation type."""
        for link in element.findall("atom:link", ns):
            if link.get("rel") == rel:
                return link.get("href")
        return None

    def _get_category(self, element: Element, ns: dict) -> Optional[str]:
        """Get primary category."""
        cat = element.find("arxiv:primary_category", ns)
        return cat.get("term") if cat is not None else None

    def search_papers(self) -> List[Dict[str, Any]]:
        """Search arXiv and return results."""
        try:
            # Build the query URL
            url = self.build_query_url()

            # Validate URL scheme and host
            parsed_url = urlparse(url)
            if parsed_url.scheme not in {"http", "https"}:
                error_msg = f"Invalid URL scheme: {parsed_url.scheme}"
                raise ValueError(error_msg)
            if parsed_url.hostname != "export.arxiv.org":
                error_msg = f"Invalid host: {parsed_url.hostname}"
                raise ValueError(error_msg)

            # Create a custom opener that only allows http/https schemes
            class RestrictedHTTPHandler(urllib.request.HTTPHandler):
                def http_open(self, req):
                    return super().http_open(req)

            class RestrictedHTTPSHandler(urllib.request.HTTPSHandler):
                def https_open(self, req):
                    return super().https_open(req)

            # Build opener with restricted handlers
            opener = urllib.request.build_opener(RestrictedHTTPHandler, RestrictedHTTPSHandler)
            urllib.request.install_opener(opener)

            # Make the request with validated URL using restricted opener
            response = opener.open(url)
            response_text = response.read().decode("utf-8")

            # Parse the response
            papers = self.parse_atom_response(response_text)
            self.status = papers
            return papers
        except (urllib.error.URLError, ValueError) as e:
            error_result = {"error": f"Request error: {e!s}"}
            self.status = error_result
            return [error_result]

    def as_dataframe(self):
        """Convert the arXiv search results to a DataFrame.
        
        Note: This requires pandas to be installed.
        
        Returns:
            DataFrame: A pandas DataFrame containing the search results.
        """
        try:
            import pandas as pd
            data = self.search_papers()
            return pd.DataFrame(data)
        except ImportError:
            print("Pandas is required to use the as_dataframe method.")
            return None

if __name__ == "__main__":
    # Example usage
    query = "large language models"
    search_component = ArXivComponent(query, max_results=5)
    
    # Search for papers
    print(f"Searching arXiv for: {query}")
    papers = search_component.search_papers()
    
    # Print results
    print(f"Found {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'])}")
        print(f"   Summary: {paper['summary'][:50]}...")
        print(f"   URL: {paper['arxiv_url']}")
        print(f"   PDF: {paper['pdf_url']}")
        print(f"   Published: {paper['published']}")
        print(f"   Category: {paper['primary_category']}")