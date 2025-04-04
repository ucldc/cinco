import django_filters

from cincoctrl.findingaids.models import FindingAid
from cincoctrl.users.models import Repository


class FindingAidFilter(django_filters.FilterSet):
    class Meta:
        model = FindingAid
        fields = {
            "repository": ["exact"],
            "collection_title": ["icontains"],
        }

    def __init__(self, *args, **kwargs):
        repo_qs = kwargs.pop("repo_qs", Repository.objects.all())
        super().__init__(*args, **kwargs)
        self.filters["repository"].field.queryset = repo_qs
