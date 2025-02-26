from django.contrib.auth.mixins import AccessMixin
from django.views.generic import DetailView
from django.views.generic import ListView
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
from cincoctrl.users.mixins import UserHasAnyRoleMixin


class UserCanAccessRecordMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        f = FindingAid.objects.get(pk=kwargs.get("pk"))
        if not request.user.is_authenticated or not request.user.has_repo_access(
            f.repository.code,
        ):
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class ManageRecordsView(UserHasAnyRoleMixin, ListView):
    model = FindingAid
    template_name = "findingaids/list_records.html"
    context_object_name = "records"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(repository__in=self.request.user.repositories())


manage_records_view = ManageRecordsView.as_view()


class RecordDetailView(UserCanAccessRecordMixin, DetailView):
    model = FindingAid
    template_name = "findingaids/record.html"


view_record = RecordDetailView.as_view()


class FindingAidCreateView(UserHasAnyRoleMixin, CreateView):
    model = FindingAid
    form_class = FindingAidForm
    template_name = "findingaids/form.html"
    verb = "Submit"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["queryset"] = self.request.user.repositories()
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.record_type = "ead"
        return super().form_valid(form)


submit_ead = FindingAidCreateView.as_view()


class FindingAidUpdateView(UserCanAccessRecordMixin, UpdateView):
    model = FindingAid
    form_class = FindingAidForm
    template_name = "findingaids/form.html"
    verb = "Update"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["queryset"] = self.request.user.repositories()
        return kwargs


update_ead = FindingAidUpdateView.as_view()


class RecordExpressMixin:
    record_type = "express"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expressrecord = self.object.expressrecord if self.object else None
        if self.request.POST:
            context["express_form"] = ExpressRecordForm(
                self.request.POST,
                instance=expressrecord,
            )
            creator_formset = CreatorInlineFormSet(
                self.request.POST,
                self.request.FILES,
                instance=expressrecord,
            )
            subject_formset = SubjectInlineFormSet(
                self.request.POST,
                self.request.FILES,
                instance=expressrecord,
            )
            revision_formset = RevisionInlineFormSet(
                self.request.POST,
                self.request.FILES,
                instance=expressrecord,
            )
        else:
            context["express_form"] = ExpressRecordForm(
                instance=expressrecord,
            )
            creator_formset = CreatorInlineFormSet(instance=expressrecord)
            subject_formset = SubjectInlineFormSet(instance=expressrecord)
            revision_formset = RevisionInlineFormSet(instance=expressrecord)

        context["creator_formset"] = creator_formset
        context["subject_formset"] = subject_formset
        context["revision_formset"] = revision_formset
        context["verb"] = self.verb
        context["record_type"] = "express"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        express_form = context["express_form"]
        creator_formset = context["creator_formset"]
        subject_formset = context["subject_formset"]
        revision_formset = context["revision_formset"]

        if (
            express_form.is_valid()
            and creator_formset.is_valid()
            and subject_formset.is_valid()
            and revision_formset.is_valid()
        ):
            self.set_findingaid_defaults(form)
            self.object = form.save()
            express_form.instance.finding_aid = form.instance
            expressrecord = express_form.save()
            creator_formset.instance = expressrecord
            creator_formset.save()
            subject_formset.instance = expressrecord
            subject_formset.save()
            revision_formset.instance = expressrecord
            revision_formset.save()
            return super().form_valid(form)

        return self.form_invalid(form)

    def set_findingaid_defaults(self, form):
        pass


class RecordExpressCreateView(UserHasAnyRoleMixin, RecordExpressMixin, CreateView):
    model = FindingAid
    form_class = ExpressFindingAidForm
    template_name = "findingaids/express_record_form.html"
    verb = "Create"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["queryset"] = self.request.user.repositories()
        return kwargs

    def set_findingaid_defaults(self, form):
        form.instance.created_by = self.request.user
        form.instance.record_type = "express"


create_record_express = RecordExpressCreateView.as_view()


class RecordExpressUpdateView(UserCanAccessRecordMixin, RecordExpressMixin, UpdateView):
    model = FindingAid
    form_class = ExpressFindingAidForm
    template_name = "findingaids/express_record_form.html"
    verb = "Update"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["queryset"] = self.request.user.repositories()
        return kwargs


update_record_express = RecordExpressUpdateView.as_view()


class RecordExpressXMLView(UserCanAccessRecordMixin, DetailView):
    model = ExpressRecord
    template_name = "findingaids/express_record.xml"

    # TODO:
    # response = HttpResponse(
    #     content_type='text/xml'
    #     headers={'Content-Disposition': 'attachment; filename="somefilename.xml"'},
    # )

    # # generate xml_data
    # ...

    # t = loader.get_template('my_template_name.xml')
    # c = {'data': xml_data}
    # response.write(t.render(c))
    # return response


view_record_express_xml = RecordExpressXMLView.as_view()


class PublishRecordView(UserCanAccessRecordMixin, DetailView):
    model = FindingAid
    template_name = "findingaids/record_published.html"

    # TODO: add logic to do the enqueuing


publish_record = PublishRecordView.as_view()


class AttachPDFView(UserCanAccessRecordMixin, UpdateView):
    model = FindingAid
    template_name = "findingaids/attach_pdf.html"
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = SuppFileInlineFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object,
            )
        else:
            context["formset"] = SuppFileInlineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if not context["formset"].is_valid():
            return self.form_invalid(form)

        context["formset"].save()

        return super().form_valid(form)


attach_pdf = AttachPDFView.as_view()
