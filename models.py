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
    attributes = models.CharField(max_length=1000)  # Can be "Has abstract"
    authors = models.CharField(max_length=20000)
    available_url = models.CharField(max_length=2000)
    type = models.CharField(max_length=200)  # Book or journal or ...
    source = models.CharField(max_length=200)  # Name of book, journal
    title = models.CharField(max_length=2000)
    db = models.CharField(max_length=200)


KNOWN_ID_TYPE = {'pubmed', 'pii', 'doi', 'pmc', 'mid', 'rid', 'eic', 'pmcid'}
