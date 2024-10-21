import uuid

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from cincoctrl.users.decorators import user_has_repo_access
from cincoctrl.users.models import Repository
from cincoctrl.findingaids.models import FindingAid

from cincoctrl.findingaids.forms import *

@login_required
def home(request):
    context = {
        'roles': request.user.userrole_set.all()
    }
    return render(request, "findingaids/home.html", context)


@user_has_repo_access
def list_records(request, repository_id, record_type):
    repo = get_object_or_404(Repository, pk=repository_id)
    context = {
        "repository": repo,
        "record_type": record_type,
        "records": FindingAid.objects.filter(
            repository__pk=repository_id,
            record_type=record_type,
        ),
    }
    return render(request, "findingaids/list_records.html", context)

def mint_ark():
    return uuid.uuid4()

def extract_from_file(f):
    # extract from <archdesc><unitittle> and <archdesc> <unitid>
    return "title", 0

@login_required
def view_record(request, record_id):
    record = get_object_or_404(FindingAid, pk=record_id)
    return render(request, "findingaids/record.html", {"record": record})

@user_has_repo_access
def upload_ead(request, repository_id):
    repo = get_object_or_404(Repository, pk=repository_id)
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.save()
            ark = mint_ark()
            title, number = extract_from_file(f)
            fa = FindingAid.objects.create(ark=ark,
                                           repository=repo,
                                           created_by=request.user,
                                           collection_title=title,
                                           collection_number=number,
                                           ead_file=f,
                                           record_type='ead')
            return HttpResponseRedirect(reverse('findingaids:list_records',
                                                kwargs={'repository_id': repo.pk,
                                                        'record_type': 'ead'}))
    else:
        form = FileForm()

    return render(request,
                  "findingaids/form.html",
                  {'form': form, 'record_type': "EAD"})


@login_required
def update_record(request, record_id):
    record = get_object_or_404(FindingAid, pk=record_id)
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.save()
            title, number = extract_from_file(f)
            record.collection_title = title
            record.collection_number = number
            record.ead_file = f
            record.save()
            return HttpResponseRedirect(reverse('findingaids:list_records',
                                                kwargs={'repository_id': record.repository.pk,
                                                        'record_type': 'ead'}))
    else:
        form = FileForm(instance=record.ead_file)

    return render(request,
                  "findingaids/form.html",
                  {'form': form, 'record_type': "EAD"})


# @login_required
# def upload_eadpdf(request, repository_id):
#     return render(request, "findingaids/form.html")


# @login_required
# def update_eadpdf(request, record_id):
#     return render(request, "findingaids/form.html")


# @login_required
# def create_record_express(request, repository_id):
#     return render(request, "findingaids/express_form.html")


# @login_required
# def edit_record_express(request, record_id):
#     return render(request, "findingaids/express_form.html")


# @login_required
# def viewxml_record_express(request, record_id):
#     return render(request, "findingaids/express_xml.html")
