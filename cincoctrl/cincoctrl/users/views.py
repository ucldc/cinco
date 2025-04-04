from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView

from cincoctrl.users.models import Repository
from cincoctrl.users.models import User


class RepositoryListView(LoginRequiredMixin, ListView):
    model = Repository
    template_name = "users/repositories.yml"

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Content-Disposition"] = 'attachment; filename="repositories.yml"'
        return response


repository_list_view = RepositoryListView.as_view()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class ChangePasswordView(PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "users/user_form.html"

    def get_success_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_change_password = ChangePasswordView.as_view()
