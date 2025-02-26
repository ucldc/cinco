from django.contrib.auth.mixins import AccessMixin

from cincoctrl.findingaids.models import FindingAid


class UserCanAccessRecordMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        f = FindingAid.objects.get(pk=kwargs.get("pk"))
        if not request.user.is_authenticated or not request.user.has_repo_access(
            f.repository.code,
        ):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
