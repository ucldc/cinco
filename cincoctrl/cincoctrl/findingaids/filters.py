import django_filters
from django.db.models import Q
from django.forms.widgets import TextInput

from cincoctrl.findingaids.models import FindingAid
from cincoctrl.users.models import Repository


class FindingAidFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method="filter_search",
        label="Search for collections",
        widget=TextInput(
            attrs={
                "placeholder": "Collection Title, Collection Number, or ARK",
                "class": "form-control me-2",
                "aria-label": "Search",
            },
        ),
    )

    class Meta:
        model = FindingAid
        fields = ["repository", "search"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(collection_title__icontains=value)
            | Q(collection_number__icontains=value)
            | Q(ark__icontains=value),
        ).distinct()

    def __init__(self, *args, **kwargs):
        repo_qs = kwargs.pop("repo_qs", Repository.objects.all())
        super().__init__(*args, **kwargs)
        self.filters["repository"].field.queryset = repo_qs
