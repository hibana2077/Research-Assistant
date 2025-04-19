import requests
import os

def download_arxiv_pdf(pdf_url, save_root_dir=None):
    """
    Download a PDF from arXiv given its URL.
    
    Args:
        pdf_url (str): The URL of the PDF on arXiv (e.g., 'https://arxiv.org/pdf/2203.02155.pdf')
        save_root_dir (str, optional): Directory where to save the PDF. If None, saves the PDF
                                     in the current directory.
    
    Returns:
        str: Path to the downloaded PDF file
    """
    try:
        # Make the request to download the PDF
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Extract the paper ID from the URL
        paper_id = pdf_url.split('/')[-1].replace('.pdf', '')
        
        # Determine the save path
        if save_root_dir is None:
            save_path = f"{paper_id}.pdf"
        else:
            # Create directories if they don't exist
            os.makedirs(save_root_dir, exist_ok=True)
            save_path = os.path.join(save_root_dir, f"{paper_id}.pdf")
        
        # Save the PDF
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"PDF successfully downloaded to {save_path}")
        return save_path
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None