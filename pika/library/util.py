"""Utility functions used in the library blueprint"""
import os.path
import random
import string
import warnings
from datetime import datetime, date
from typing import List

from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename

from pika.api import BookData
from .forms import AddBookForm, EditBookForm


def generate_pages(page: int, offset: int, last_page: int) -> List[int | str]:
    """
    Generate a list of pages with ``page`` in the middle and an ``offset`` amount of pages left and right.
    The minimum page is 1 and the maximum page is ``last_page``. Includes a period on positions to indicate
    more/missing pages.
    :param page: Current page/Page at the center of list.
    :type page: int
    :param offset: Amount of next and previous pages to be shown.
    :type offset: int
    :param last_page: Highest page to be shown in return list.
    :type last_page: int
    :return: List of page numbers.
    :rtype: List[int | str]
    """
    all_pages = range(1, last_page + 1)
    if page - offset <= 0:
        displayed_pages = range(max(page - offset, 1), max(2 * offset + 3, page + offset + 1))
    else:
        displayed_pages = range(min(page - offset, last_page - (2 * offset + 1)),
                                max(2 * offset + 3, page + offset + 1))

    pages = []
    prev = None
    for _page in all_pages:
        if _page == 1 or _page == last_page or _page in displayed_pages:
            # print(page)
            pages.append(_page)
            prev = _page
        else:
            if prev != ".":
                pages.append(".")
            prev = "."
    return pages


def generate_filename(book_id: int, filename: str):
    """
    Generate a filename based on a book id and the original filename.
    :param book_id: Book ID
    :type book_id: int
    :param filename: Original filename
    :type filename: str
    :return: Filename which includes timestamp, book ID, a random string and the original filename.
    :rtype: str
    """
    random_string = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    s_filename = secure_filename(filename)
    s_filename = s_filename.replace("-", "")
    return f"{timestamp}-{book_id}-{random_string}-{s_filename}"


def put_book_payload(form: AddBookForm | EditBookForm, book_data: BookData) -> dict[str, str]:
    """
    Get, compare payloads and prepare book payload for PUT API request.
    :param form: Form with updated book data.
    :type form: AddBookForm | EditBookForm
    :param book_data: Original book data.
    :type book_data: BookData
    :return: Book payload for PUT API request.
    :rtype: dict[str, str]
    """
    form_payload = form.api_payload()
    book_payload = book_data.api_payload()

    # If file is provided always replace, if none is provided never update, identical files get replaced
    if form_payload["cover"]:
        form_payload.update({
            "cover": os.path.join("covers", generate_filename(book_data.book_id, form_payload["cover"].filename))
        })
    else:
        form_payload.update({"cover": book_payload["cover"]})

    if form_payload == book_payload:
        return book_payload

    return form_payload


def parse_goodreads_soup(page_soup: BeautifulSoup) -> dict[str, str]:
    """
    Parse HTML page soup from goodreads.com
    :param page_soup: HTML page soup
    :type page_soup: BeautifulSoup
    :return: Dictionary of Goodreads book data
    :rtype: dict[str, str]
    """
    main = page_soup.find(name="main")
    title_section = page_soup.find(name="div", attrs={"class": "BookPageTitleSection"})

    goodreads_data = {}

    title = title_section.find(name="h1", attrs={"data-testid": "bookTitle"}).get_text()
    goodreads_data.update({"title": title})

    series = title_section.find(name="h3").get_text()
    series_title, _, volume_nr = series.partition("#")
    volume_nr = float(volume_nr)
    goodreads_data.update({"series_title": series_title, "volume_nr": volume_nr})

    author_name = main.find(name="span", attrs={"data-testid": "name"}).get_text()
    goodreads_data.update({"author_name": author_name})

    release_date = main.find(name="p", attrs={"data-testid": "publicationInfo"}).get_text()
    release_date_datetime = datetime.strptime(release_date, "First published %B %d, %Y")
    goodreads_data.update({"release_date": release_date_datetime})

    synopsis = main.find(name="div", attrs={"data-testid": "contentContainer"})
    synopsis = "\n".join(synopsis.strings)
    goodreads_data.update({"synopsis": synopsis})

    cover = main.find(name="img").attrs["src"]
    goodreads_data.update({"cover": cover})

    return goodreads_data


def parse_release_date(iso_string: str) -> datetime:
    """Parse book release date from ISO string returned by pika app API."""
    warnings.warn("This function is deprecated, use `date` instead", DeprecationWarning)
    input_format = "%a, %d %b %Y %H:%M:%S %Z"
    return datetime.strptime(iso_string, input_format)


def put_book_payload_from_form(form_data):
    """Generate payload for API based on web form."""
    warnings.warn("This function is deprecated, use `form.api_payload` instead", DeprecationWarning)
    payload = {
        "title": form_data['title'],
        "release_date": form_data['release_date'].isoformat(),
        "synopsis": form_data['synopsis'],
        "read_status": form_data['read_status'],
        "authors": [{"author_id": int(_id)} for _id in form_data['authors']],
        "cover": form_data['cover'],
        "volume_nr": form_data['volume_nr'] and float(form_data['volume_nr']),
    }

    if form_data["series"]:
        payload.update({"series": {"series_id": int(form_data["series"])}})
    else:
        payload.update({"series": None})

    return payload


def put_book_payload_from_api(book_data):
    """Generate payload for API based on data returned by pika app API."""
    warnings.warn("This function is deprecated, use `form.api_payload` instead", DeprecationWarning)
    payload = {
        "title": book_data['title'],
        "release_date": date.fromisoformat(book_data['release_date']).isoformat(),
        "synopsis": book_data['synopsis'],
        "read_status": book_data['read_status'],
        "authors": [{"author_id": int(_author["author_id"])} for _author in book_data['authors']],
        "cover": book_data['cover'],
        "volume_nr": book_data['volume_nr'] and float(book_data['volume_nr']),
    }
    if book_data["series"]:
        payload.update({"series": {"series_id": int(book_data["series"]["series_id"])}})
    else:
        payload.update({"series": None})

    return payload
