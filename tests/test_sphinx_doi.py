import exmemo.sphinx.doi as _ex
import json

def test_get_citation_cache(tmp_path):
    doi = '00.0000/0000000'
    cache = {
            doi: {
                'authors': [
                    {'given': 'Alice', 'family': 'Adams'},
                    {'given': 'Bob', 'family': 'Brown'},
                ],
                'title': "A new method for frobnicating widgets",
                'journal': "Journal of Widget Frobnication",
                'issue': None,
                'year': 2024,
                'url': 'example.com',
            },
    }
    cache_path = tmp_path / 'doi.json'

    with open(cache_path, 'w') as f:
        json.dump(cache, f)

    assert _ex.get_citation(doi, cache_path) == _ex.Citation(
            authors=[
                _ex.Author(given='Alice', family='Adams'),
                _ex.Author(given='Bob', family='Brown'),
            ],
            title="A new method for frobnicating widgets",
            journal="Journal of Widget Frobnication",
            issue=None,
            year=2024,
            url='example.com',
    )

def test_get_citation_from_crossref():
    c = _ex.get_citation_from_crossref('10.1145/3065386')

    assert c.authors == [
            _ex.Author(given='Alex', family='Krizhevsky'),
            _ex.Author(given='Ilya', family='Sutskever'),
            _ex.Author(given='Geoffrey E.', family='Hinton'),
    ]
    assert c.title == "ImageNet classification with deep convolutional neural networks"
    assert c.journal == "Communications of the ACM"
    assert c.issue == "60:6:84-90"
    assert c.year == 2017
    assert c.url == 'http://dx.doi.org/10.1145/3065386'

def test_get_citation_from_datacite():
    c = _ex.get_citation_from_datacite('10.48550/arXiv.1706.03762')

    assert c.authors == [
            _ex.Author(given='Ashish', family='Vaswani'),
            _ex.Author(given='Noam', family='Shazeer'),
            _ex.Author(given='Niki', family='Parmar'),
            _ex.Author(given='Jakob', family='Uszkoreit'),
            _ex.Author(given='Llion', family='Jones'),
            _ex.Author(given='Aidan N.', family='Gomez'),
            _ex.Author(given='Lukasz', family='Kaiser'),
            _ex.Author(given='Illia', family='Polosukhin'),
    ]
    assert c.title == "Attention Is All You Need"
    assert c.journal == "arXiv"
    assert c.issue == None
    assert c.year == 2017
    assert c.url == 'https://arxiv.org/abs/1706.03762'

def test_citation_from_dict():
    c = _ex.Citation(
            authors=[
                _ex.Author(given='Alice', family='Adams'),
                _ex.Author(given='Bob', family='Brown'),
            ],
            title="A new method for frobnicating widgets",
            journal="Journal of Widget Frobnication",
            issue=None,
            year=2024,
            url='example.com',
    )
    d = {
            'authors': [
                {'given': 'Alice', 'family': 'Adams'},
                {'given': 'Bob', 'family': 'Brown'},
            ],
            'title': "A new method for frobnicating widgets",
            'journal': "Journal of Widget Frobnication",
            'issue': None,
            'year': 2024,
            'url': 'example.com',
    }

    assert _ex.dict_from_citation(c) == d
    assert _ex.citation_from_dict(d) == c


def test_strip_html():
    assert _ex.strip_html('Hello World') == 'Hello World'
    assert _ex.strip_html('Hello <b>World</b>') == 'Hello World'
    assert _ex.strip_html('Hello &amp; World') == 'Hello & World'
