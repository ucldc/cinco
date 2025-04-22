import requests
from django.core.files.base import ContentFile


def download_pdf(url, filename):
    response = requests.get(
        url,
        stream=True,
        headers={"Accept": "application/pdf"},
        timeout=30,
    )
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    file_content = b""
    for chunk in response.iter_content(chunk_size=None):
        file_content += chunk
    return ContentFile(file_content, name=filename)
