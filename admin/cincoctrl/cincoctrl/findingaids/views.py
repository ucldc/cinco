from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView

from cincoctrl.findingaids.forms import CreatorInlineFormSet
from cincoctrl.findingaids.forms import ExpressFindingAidForm
from cincoctrl.findingaids.forms import ExpressRecordForm
from cincoctrl.findingaids.forms import FindingAidForm
from cincoctrl.findingaids.forms import RevisionInlineFormSet
from cincoctrl.findingaids.forms import SubjectInlineFormSet
from cincoctrl.findingaids.forms import SuppFileInlineFormSet
from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.users.mixins import UserHasRepoAccessMixin
from cincoctrl.users.models import Repository


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = "findingaids/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = self.request.user.userrole_set.all()
        return context


home = HomePageView.as_view()


class FindingAidListView(UserHasRepoAccessMixin, ListView):
    model = FindingAid
    template_name = "findingaids/list_records.html"
    context_object_name = "records"

    def get(self, request, *args, **kwargs):
        self.repository = get_object_or_404(Repository, code=kwargs.get("repo_slug"))
        self.record_type = kwargs.get("record_type")
        return super().get(request, args, kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(repository=self.repository, record_type=self.record_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["repository"] = self.repository
        context["record_type"] = self.record_type
        return context


record_list_view = FindingAidListView.as_view()


class RecordDetailView(UserHasRepoAccessMixin, DetailView):
    model = FindingAid
    template_name = "findingaids/record.html"


view_record = RecordDetailView.as_view()


class FindingAidMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.repository = get_object_or_404(Repository, code=kwargs.get("repo_slug"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.record_type == "ead_pdf":
            if self.request.POST:
                context["formset"] = SuppFileInlineFormSet(
                    self.request.POST,
                    self.request.FILES,
                    instance=self.object,
                )
            else:
                context["formset"] = SuppFileInlineFormSet(instance=self.object)
        context["repository"] = self.repository
        context["verb"] = self.verb
        context["record_type"] = self.record_type
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if "formset" in context:
            formset = context["formset"]
            if formset.is_valid():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                return super().form_valid(form)
            return self.form_invalid(form)
        return super().form_valid(form)


class FindingAidCreateView(UserHasRepoAccessMixin, FindingAidMixin, CreateView):
    model = FindingAid
    form_class = FindingAidForm
    template_name = "findingaids/form.html"
    verb = "Upload"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.record_type = kwargs.get("record_type")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.repository = self.repository
        form.instance.record_type = self.record_type
        return super().form_valid(form)


upload_record = FindingAidCreateView.as_view()


class FindingAidCreateView(UserHasRepoAccessMixin, FindingAidMixin, CreateView):
    model = FindingAid
    form_class = FindingAidForm
    template_name = "findingaids/form.html"
    verb = "Upload"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.record_type = kwargs.get("record_type")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.repository = self.repository
        form.instance.record_type = self.record_type
        return super().form_valid(form)


upload_record = FindingAidCreateView.as_view()


class FindingAidUpdateView(UserHasRepoAccessMixin, FindingAidMixin, UpdateView):
    model = FindingAid
    form_class = FindingAidForm
    template_name = "findingaids/form.html"
    verb = "Update"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.record_type = self.get_object().record_type


update_record = FindingAidUpdateView.as_view()


class RecordExpressMixin:
    record_type = "express"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.repository = get_object_or_404(Repository, code=kwargs.get("repo_slug"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formsets = []
        fa_form = self.get_findingaid_form()
        if self.request.POST:
            formsets.append(
                CreatorInlineFormSet(
                    self.request.POST,
                    self.request.FILES,
                    instance=self.object,
                ),
            )
            formsets.append(
                SubjectInlineFormSet(
                    self.request.POST,
                    self.request.FILES,
                    instance=self.object,
                ),
            )
            formsets.append(
                RevisionInlineFormSet(
                    self.request.POST,
                    self.request.FILES,
                    instance=self.object,
                ),
            )
            formsets.append(
                SuppFileInlineFormSet(
                    self.request.POST,
                    self.request.FILES,
                    instance=fa_form.instance,
                ),
            )
        else:
            formsets.append(CreatorInlineFormSet(instance=self.object))
            formsets.append(SubjectInlineFormSet(instance=self.object))
            formsets.append(RevisionInlineFormSet(instance=self.object))
            formsets.append(SuppFileInlineFormSet(instance=fa_form.instance))

        context["finding_aid_form"] = fa_form
        context["formsets"] = formsets
        context["repository"] = self.repository
        context["verb"] = self.verb
        context["record_type"] = "express"
        return context

    def get_findingaid_form(self):
        if self.request.POST:
            form = ExpressFindingAidForm(self.request.POST)
        else:
            form = ExpressFindingAidForm()
        return form

    def set_findingaid_defaults(self, form):
        pass

    def form_valid(self, form):
        context = self.get_context_data()
        fa_form = context["finding_aid_form"]
        if fa_form.is_valid():
            self.set_findingaid_defaults(fa_form)
            finding_aid = fa_form.save()
            form.instance.finding_aid = finding_aid
            formsets_valid = True
            for formset in context.get("formsets", []):
                if not formset.is_valid():
                    formsets_valid = False

            if formsets_valid:
                self.object = form.save()
                for formset in context.get("formsets", []):
                    if isinstance(formset, SuppFileInlineFormSet):
                        formset.instance = finding_aid
                    else:
                        formset.instance = self.object
                    formset.save()
                return super().form_valid(form)

        return self.form_invalid(form)


class RecordExpressCreateView(UserHasRepoAccessMixin, RecordExpressMixin, CreateView):
    model = ExpressRecord
    form_class = ExpressRecordForm
    template_name = "findingaids/express_record_form.html"
    verb = "Create"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.repository = get_object_or_404(Repository, code=kwargs.get("repo_slug"))

    def set_findingaid_defaults(self, form):
        form.instance.created_by = self.request.user
        form.instance.repository = self.repository
        form.instance.record_type = "express"


create_record_express = RecordExpressCreateView.as_view()


class RecordExpressUpdateView(UserHasRepoAccessMixin, RecordExpressMixin, UpdateView):
    model = ExpressRecord
    form_class = ExpressRecordForm
    template_name = "findingaids/express_record_form.html"
    verb = "Update"

    def get_findingaid_form(self):
        if self.request.POST:
            form = ExpressFindingAidForm(
                self.request.POST,
                instance=self.object.finding_aid,
            )
        else:
            form = ExpressFindingAidForm(instance=self.object.finding_aid)
        return form


update_record_express = RecordExpressUpdateView.as_view()


class RecordExpressDetailView(UserHasRepoAccessMixin, DetailView):
    model = ExpressRecord
    template_name = "findingaids/express_record.html"


view_record_express = RecordExpressDetailView.as_view()


class RecordExpressXMLView(UserHasRepoAccessMixin, DetailView):
    model = ExpressRecord
    template_name = "findingaids/express_record.xml"


view_record_express_xml = RecordExpressXMLView.as_view()
