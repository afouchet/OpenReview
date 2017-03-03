import ast
from collections import defaultdict
from redis import StrictRedis
import requests

from ..models import Publication, KNOWN_ID_TYPE


REDIS_DB = StrictRedis(db=0)

def request_cache(url, params=None, ttl_callback=None):
    redis_key = url + 'params=' + str(params)
    res = REDIS_DB.get(redis_key)
    if res:
        # Json doesn't handle single quote encoding
        # Need to use ast
        return ast.literal_eval(res)

    res = requests.get(url, params=params).json()
    if not ttl_callback:
        ttl = 3600 * 24 * 31
    else:
        ttl = ttl_callback(res)
    # ex is the ttl in seconds
    REDIS_DB.set(redis_key, res, ex=ttl)
    return res

def get_publications(search_query, page=0, page_size=20, db='pubmed'):
    """
    Get PubMed answer to search query, then loads the article from our database
    or we get them from pubmed's database
    """
    publication_ids, nb_publi = _get_publication_ids(search_query, page, page_size, db)
    return nb_publi, _get_publication(publication_ids, db)


def get_similars(article_id, db='pubmed'):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?'
    url += 'db={db}&id={article_id}&cmd=neighbor_score&retmode=json'.format(db=db, article_id=article_id)

    def ttl(result):
        try:
            # Do we have the info we want ?
            nana = result['linksets'][0]['linksetdbs'][0]['links'][0]['id']
        except KeyError, IndexError:
            return 3600
        return 3600 * 24 * 31

    res = request_cache(url, params=PARAMS, ttl_callback=ttl)['linksets'][0]

    article_ids = list()
    article_tags = defaultdict(list)
    for links in res['linksetdbs']:
        tag = links['linkname']
        for article in links['links']:
            article_id = str(article['id'])
            article_ids.append(article_id)
            article_tags[article_id].append(tag)

    publications = _get_publication(set(article_ids), db)
    publi_dict = {p.id_pubmed: p for p in publications}
    my_tag = {p.id: article_tags.get(p.id_pubmed) for p in publications}

    seen_ids = set()
    publis_sorted = list()
    for pubmed_id in article_ids:
        if pubmed_id not in seen_ids:
            seen_ids.add(pubmed_id)
            publis_sorted.append(publi_dict[pubmed_id])

    return publis_sorted, my_tag


def _get_publication_ids(search_query, page=0, page_size=20, db='pubmeb'):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
    url += 'db={db}&&term={search_query}&retstart={offset}&retmax={page_size}&retmode=json'.format(
        db=db, search_query=search_query, offset=page * page_size, page_size=page_size)
    res = request_cache(url, params=PARAMS)['esearchresult']
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
    res = request_cache(url, params=PARAMS)['result']
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
        publication.abstract = request.get(url, params=PARAMS).content
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


