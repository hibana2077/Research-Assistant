import os
from typing import Optional
import requests

def download_arxiv_pdf(
    pdf_url: str,
    save_root_dir: Optional[str] = None,
    timeout: tuple[float, float] = (10, 60),
) -> Optional[str]:
    """Download a PDF from arXiv.

    Args:
        pdf_url: Direct link to the PDF (e.g., "https://arxiv.org/pdf/2203.02155.pdf").
        save_root_dir: Directory where the PDF should be saved. If *None*, the file is
            saved in the current working directory.
        timeout: A tuple ``(connect_timeout, read_timeout)`` in seconds.

    Returns:
        The absolute path to the downloaded file on success; *None* otherwise.
    """
    try:
        # Issue the request and validate the HTTP response.
        with requests.get(
            pdf_url, stream=True, timeout=timeout, allow_redirects=True
        ) as response:
            response.raise_for_status()

            # Basic MIME‑type validation.
            content_type = response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower():
                raise ValueError(f"Unexpected content type: {content_type}")

            # Derive a file name from the URL.
            paper_id = os.path.basename(pdf_url.split("?")[0]).removesuffix(".pdf")
            if save_root_dir:
                os.makedirs(save_root_dir, exist_ok=True)
                save_path = os.path.join(save_root_dir, f"{paper_id}.pdf")
            else:
                save_path = os.path.abspath(f"{paper_id}.pdf")

            # Stream the response to disk while tracking size.
            expected_size = int(response.headers.get("Content-Length", "0"))
            written = 0
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep‑alive chunks.
                        file.write(chunk)
                        written += len(chunk)

            # Guard against truncated downloads.
            if expected_size and written != expected_size:
                raise IOError(
                    f"Incomplete download: expected {expected_size} bytes, got {written} bytes"
                )

        print(f"PDF successfully downloaded to {save_path}")
        return save_path

    except (requests.RequestException, ValueError, IOError) as error:
        print(f"Download failed: {error}")
        return None
    
if __name__ == "__main__":
    # Example usage
    pdf_url = "http://arxiv.org/pdf/1809.10784v1"
    download_arxiv_pdf(pdf_url, save_root_dir="papers")