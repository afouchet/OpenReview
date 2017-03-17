from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render

from .models import Profile, User, Publication, PubliComment
from .services import fetch_publications

def test(request):
    return render(request, 'open_review/test_2.html')


def build_advanced_search(request):
    return render(request, 'open_review/advanced_search.html')


def advanced_search(request):
    if not request.POST['field[]']:
        # Empty request
        return render(request, 'open_review/advanced_search.html')

    fields = request.POST.getlist('field[]')
    texts = request.POST.getlist('criteria[]')
    links = request.POST.getlist('link[]', [])

    search_query = texts.pop(0)
    field = fields.pop(0)
    if field != "All Fields":
        search_query += '[' + field + ']'

    for link, field, text in zip(links, fields, texts):
        search_query = '({old_query}) {link} {text}'.format(old_query=search_query, link=link, text=text)
        if field != "All Fields":
            search_query += '[' + field + ']'

    request.POST = request.POST.copy()
    request.POST['search_query'] = search_query
    return search(request)


def welcome(request):
    return render(request, 'open_review/welcome.html')


def create_profile_form(request, errors=None):
    return render(request, 'open_review/create_profile.html', {'errors': errors})


def created_profile(request):
    # Handling errors (name already taken, invalid email)
    errors = []
    if User.objects.filter(username=request.POST['username']).count():
        errors.append('username')
    try:
        validate_email(request.POST['email'])
    except ValidationError:
        errors.append('email')
    if errors:
        print(errors)
        return create_profile_form(request, errors)
    user = User.objects.create_user(
        username=request.POST['username'],
        email=request.POST['email'],
        password=request.POST['password'],
    )
    profile = Profile(user=user)
    profile.first_name = request.POST['first_name']
    profile.last_name = request.POST['last_name']
    profile.university = request.POST['university']
    profile.save()
    return log(request, next_page='open_review:homepage')
    

def log(request, next_page='open_review:homepage'):
    user = authenticate(username=request.POST['username'],
                        password=request.POST['password'])
    if not user:
        return render(request, 'open_review/login.html',
                      {'errors': 'Wrong username or password'})
    login(request, user)
    # Hack: you are returning on Dolead's result page
    return HttpResponseRedirect(reverse(next_page))



def api_login(request):
    return render(request, 'open_review/login.html')


@login_required(login_url='/swear_jar/login/')
def change_password(request):
    if not request.user.check_password(request.POST['old']):
        render(request, 'open_review/edit_player.html')
    if request.POST['new'] == request.POST['repeat']:
        request.user.set_password(request.POST['new'])
    return render(request, 'open_review/welcome.html')


@login_required(login_url='/open_review/login/')
def edit_profile_form(request):
    return render(request, 'open_review/edit_profile.html', {
            'profile': request.user.profile,
            })


@login_required(login_url='/swear_jar/login/')
def edited_profile(request):
    if request.POST.get('last_name'):
        request.user.profile.last_name = request.POST['last_name']
    if request.POST.get('first_name'):
        request.user.profile.first_name = request.POST['first_name']
    if request.POST.get('university'):
        request.user.profile.university = request.POST['university']
    if request.POST.get('email'):
        email = request.POST['email']
        try:
            validate_email(email)
            request.user.email = email
            request.user.save()
        except ValidationError:
            pass
    request.user.profile.save()
    return render(request, 'open_review/edit_profile.html')


def search(request):
    nb_publi, publications = fetch_publications.get_publications(
        search_query=request.POST['search_query'],
        page=int(request.POST['page']),
        page_size=int(request.POST['page_size']))
    # Make function to display rating for each publication
    page = int(request.POST['page'])
    page_size = int(request.POST['page_size'])
    first_pub = page * page_size + 1
    last_pub = (page + 1) * page_size
    return render(request, 'open_review/search.html', {
        'nb_publi': nb_publi,
        'first_pub': first_pub,
        'last_pub': last_pub,
        'publications': publications,
        'next_page': page + 1,
        'search_query': request.POST['search_query'],
        'page_size': page_size,
    })
    

def publication_detail(request, publi_id):
    publication = Publication.objects.get(pk=publi_id)
    comments = publication.publicomment_set.all()
    nb_comments = comments.count()
    if not nb_comments:
        rating_overall = 0
        rating_field_contribution = 0
        rating_methodology = 0
    else:
        rating_overall = sum(comment.rating_overall for comment in comments) / nb_comments
        rating_field_contribution = sum(comment.rating_field_contribution for comment in comments) / nb_comments
        rating_methodology = sum(comment.rating_methodology for comment in comments) / nb_comments
    
    try:
        publis_similar, publi_tags = fetch_publications.get_similars(publication.id_pubmed)
    except KeyError, IndexError:
        publis_similar = []
        publi_tags = {}
    similars = [(publi, publi_tags[publi.id]) for publi in publis_similar[:5]]
    return render(request, 'open_review/desc_publi.html', {
        'publication': publication,
        'similars': similars,
        'abstract': fetch_publications.get_abstract(publi),
        'rating_overall': rating_overall,
        'rating_field_contribution': rating_field_contribution,
        'rating_methodology': rating_methodology,
        })


def api_full_text_link(request, publi_id):
    return JsonResponse({'link': fetch_publications.get_full_text_link(publi_id)})


def comment_publi(request, publi_id):
    publi = Publication.objects.get(pk=publi_id)
    comment = PubliComment(
        publication=publi,
        author=request.user.profile,
        text=request.POST['comment'],
        rating_overall=request.POST['rating_overall'],
        rating_field_contribution=request.POST['rating_field_contribution'],
        rating_methodology=request.POST['rating_methodology'],
    ).save()
    rating = float(request.POST['rating_overall'])
    publi.rating = (publi.rating * publi.nb_comments + rating) / (publi.rating + 1)
    publi.nb_comments += 1
    publi.save()
    return publication_detail(request, publi_id)


@login_required(login_url='/open_review/login/')
def api_logout(request):
    logout(request)
    # Hack: you are returning on Dolead's result page
    return HttpResponseRedirect(reverse('open_review:login'))
