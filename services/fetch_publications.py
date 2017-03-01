import requests

from ..models import Publication, KNOWN_ID_TYPE


def get_publications(search_query, page=0, page_size=20, db='pubmed'):
    """
    Get PubMed answer to search query, then loads the article from our database
    or we get them from pubmed's database
    """
    publication_ids, nb_publi = _get_publication_ids(search_query, page, page_size, db)
    return nb_publi, _get_publication(publication_ids, db)


def _get_publication_ids(search_query, page=0, page_size=20, db='pubmeb'):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
    url += 'db={db}&&term={search_query}&retstart={offset}&retmax={page_size}&retmode=json'.format(
        db=db, search_query=search_query, offset=page * page_size, page_size=page_size)
    res = requests.get(url, params=PARAMS).json()['esearchresult']
    id_list = res['idlist']
    nb_publi = res['count']
    return id_list, nb_publi


def _get_publication(publication_ids, db):
    # Stored publication
    publication_dict = {p.id_pubmed: p for p in Publication.objects.filter(id_pubmed__in=publication_ids)}
    missing_ids = [pid for pid in publication_ids if pid not in publication_dict]
    if missing_ids:
        publi_missing = _load_publication(missing_ids, db)
        publication_dict.update({p.id_pubmed: p for p in publi_missing})
    return [publication_dict[pid] for pid in publication_ids]


def _load_publication(publication_ids, db):
    url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?'
    url += 'db={db}&retmode=json&rettype=abstract&id={id_list}'.format(
        db=db, id_list=','.join(publication_ids))
    res = requests.get(url, params=PARAMS).json()['result']
    res.pop('uids', None)
    return [_save_publi(publi_json, db) for publi_json in res.values()]
    

def _save_publi(publi_json, db):
    publi = Publication()
    for id_desc in publi_json['articleids']:
        if id_desc['idtype'] in KNOWN_ID_TYPE:
            setattr(publi, 'id_' + id_desc['idtype'], id_desc['value'])
    publi.attributes = ';'.join(publi_json.get('attributes', []))
    publi.authors = ', '.join(auth['name'] for auth in publi_json['authors']
                              if auth['authtype'] == 'Author')
    publi.available_url = publi_json['availablefromurl']
    publi.pub_date = publi_json['pubdate']
    publi.type = publi_json['pubtype']
    publi.source = publi_json['source']
    publi.title = publi_json['title']
    publi.db = db
    publi.save()
    return publi


def get_abstract(publication):
    if 'Has Abstract' not in publication.attributes:
        return 'Not available'
    if not publication.abstract:
        url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'
        url += 'db={db}&retmode=text&rettype=abstract&id={id}'.format(
            db=publication.db, id=getattr(publication, 'id_' + publication.db))
        publication.abstract = requests.get(url, params=PARAMS).content
        publication.summary = summarize_abstract(publication.abstract)
        publication.save()
    return publication.abstract
    
PARAMS = {'email': 'arnaud.fouchet@dolead.com', 'tool': 'OpenReview'}
    
def summarize_abstract(abstract):
    """
    Pubmeb always returns abstract in this format:
    "
    ''
    Journal
    ''
    Title
    ''
    Authors
    ''
    Author information
    ''
    real abstract
    ''
    DOI
    PMID
    ''
    ''
    """
    blanks = 0
    lines = []
    for line in abstract.split('\n'):
        if line == u'':
            blanks += 1
        elif blanks == 5:
            lines.append(line)

    return '\n'.join(lines)


