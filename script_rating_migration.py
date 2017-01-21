from OpenReview.models import Publication

for publi in Publication.objects.all():
    for comment in publi.publicomment_set.all():
        publi.rating += comment.rating_overall
        publi.nb_comments += 1
    if publi.nb_comments:
        publi.rating /= publi.nb_comments
        publi.save()
