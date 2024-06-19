import requests
import json

from .. import app
from docutils import nodes as n
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Author:
    family: str
    given: str

@dataclass
class Citation:
    authors: list[Author]
    title: Optional[str]
    journal: Optional[str]
    issue: Optional[str]
    year: Optional[int]
    url: Optional[str]

def doi_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Insert a citation (including the authors, title, journal, and publication 
    date) given any valid DOI.

    For example:
        :doi:`10.1093/nar/gkw908`
    """

    cache_path = Path(app.user_cache_dir) / 'doi.json'

    try:
        citation = get_citation(text, cache_path)
    except CitationError as err:
        warning = inliner.reporter.warning(str(err))
        p = n.paragraph(text, text)
        return [p], [warning]

    def format_authors(citation):
        authors = [format_author(x) for x in citation.authors]

        if len(authors) == 1:
            return authors[0]
        elif len(authors) < 5:
            return ", ".join(x for x in authors[:-1]) + " & " + authors[-1]
        else:
            return f"{authors[0]} et al"

    def format_author(author):
        initials = ''.join(x[0] for x in author.given.split())
        return f"{author.family} {initials}"

    def format_title(citation):
        if citation.title is None:
            return '[html]'

        title = strip_html(citation.title.strip())

        if title[-1] in ['.', '!', '?']:
            return title
        else:
            return title + '.'

    def format_journal_issue_date(citation):
        parts = [
                citation.journal,
                citation.issue,
                f'({y})' if (y := citation.year) else None,
        ]
        return ' '.join(x for x in parts if x)


    a = n.reference(refuri=citation.url)
    a += [
            n.emphasis(x := format_title(citation) + ' ', x)
    ]
    p = [
            n.Text(format_authors(citation) + '. '),
            a,
            n.Text(format_journal_issue_date(citation)),
    ]
    return p, []

def get_citation(doi, cache_path):
    cache = {}

    if cache_path.exists():
        with cache_path.open() as f:
            cache = json.load(f)

    if doi in cache:
        return citation_from_dict(cache[doi])

    citation = None
    errors = []

    try:
        citation = get_citation_from_crossref(doi)
    except CitationError as err:
        errors.append(str(err))

        try:
            citation = get_citation_from_datacite(doi)
        except CitationError as err:
            errors.append(str(err))

    if citation is None:
        raise CitationError('\n'.join(errors))

    cache[doi] = dict_from_citation(citation)

    cache_path.parent.mkdir(exist_ok=True)
    with cache_path.open('w') as f:
        json.dump(cache, f)

    return citation

def get_citation_from_crossref(doi):
    try:
        r = requests.get('https://api.crossref.org/works/' + doi)
    except requests.RequestException as err:
        raise CitationError(f"unable to connect to CrossRef: {err}")

    if r.status_code == 404:
        raise CitationError(f"DOI not found in CrossRef: {doi}")

    d = r.json()['message']

    try:
        title = d['title'][0]
    except IndexError:
        title = None

    try:
        journal = d['container-title'][0]
    except (KeyError, IndexError):
        journal = None
        issue = None
    else:
        issue = ':'.join(
                d[k] for k in ('volume', 'issue', 'page')
                if k in d
        )

    try:
        year = d['issued']['date-parts'][0][0]
    except (KeyError, IndexError):
        year = None

    try:
        url = d['URL']
    except (KeyError, IndexError):
        url = None

    return Citation(
            authors=[
                Author(
                    family=author['family'],
                    given=author['given'],
                )
                for author in d['author']
            ],
            title=title,
            journal=journal,
            issue=issue,
            year=year,
            url=url,
    )

def get_citation_from_datacite(doi):
    try:
        r = requests.get('https://api.datacite.org/dois/' + doi)
    except requests.RequestException as err:
        raise CitationError(f'unable to connect to DataCite: {err}')

    if r.status_code == 404:
        raise CitationError(f"DOI not found in DataCite: {doi}")

    d = r.json()['data']['attributes']

    return Citation(
            authors=[
                Author(
                    family=creator['familyName'],
                    given=creator['givenName'],
                )
                for creator in d['creators']
            ],
            title=d['titles'][0]['title'],
            journal=d['publisher'],
            issue=None,
            year=int(d['published']),
            url=d['url'],
    )

def dict_from_citation(citation):
    return asdict(citation)

def citation_from_dict(d):
    d['authors'] = [
            Author(**author)
            for author in d['authors']
    ]
    return Citation(**d)

def strip_html(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, features='html.parser')
    return soup.get_text()

class CitationError(RuntimeError):

    def __init__(self, message, try_other_servers=False):
        super().__init__(message)
        self.try_other_servers = try_other_servers

def setup(app):
    app.add_role('doi', doi_role)

