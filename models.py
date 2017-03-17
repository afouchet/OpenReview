from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    university = models.CharField(max_length=200)
    certified_scientist = models.BooleanField(default=False)


class Publication(models.Model):
    id_pubmed = models.CharField(max_length=200)
    id_pii = models.CharField(max_length=200)
    id_doi = models.CharField(max_length=200)
    id_pmc = models.CharField(max_length=200)
    id_mid = models.CharField(max_length=200)
    id_rid = models.CharField(max_length=200)
    id_eic = models.CharField(max_length=200)
    id_pmcid = models.CharField(max_length=200)
    abstract = models.CharField(max_length=5000)  # Can be "Has abstract"
    attributes = models.CharField(max_length=1000)  # Can be "Has abstract"
    authors = models.CharField(max_length=20000)
    available_url = models.CharField(max_length=2000)
    db = models.CharField(max_length=200)
    nb_comments = models.IntegerField(default=0)
    pub_date = models.CharField(max_length=50)
    rating = models.FloatField(default=0)
    source = models.CharField(max_length=200)  # Name of book, journal
    summary = models.CharField(max_length=5000, default='')  # Can be "Has abstract"
    title = models.CharField(max_length=2000)
    type = models.CharField(max_length=200)  # Book or journal or ...

    def dump(self):
        fields = ['id', 'title', 'authors', 'source', 'pub_date']
        return {f: getattr(self, f) for f in fields}


KNOWN_ID_TYPE = {'pubmed', 'pii', 'doi', 'pmc', 'mid', 'rid', 'eic', 'pmcid'}


RATINGS = [(i / 10., i / 10.) for i in range(51)]

class PubliComment(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    text = models.CharField(max_length=2000)
    rating_overall = models.FloatField(choices=RATINGS)
    rating_field_contribution = models.FloatField(choices=RATINGS)
    rating_methodology = models.FloatField(choices=RATINGS)
