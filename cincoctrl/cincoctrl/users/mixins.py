from django.contrib.auth.mixins import AccessMixin


class UserHasRepoAccessMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        repo_slug = kwargs.get("repo_slug")
        if not request.user.is_authenticated or not request.user.has_repo_access(
            repo_slug,
        ):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
