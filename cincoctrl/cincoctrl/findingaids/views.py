from dal.autocomplete import Select2QuerySetView
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.forms import ModelForm
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView

from cincoctrl.findingaids.filters import FindingAidFilter
from cincoctrl.findingaids.forms import CreatorInlineFormSet
from cincoctrl.findingaids.forms import ExpressFindingAidForm
from cincoctrl.findingaids.forms import ExpressRecordForm
from cincoctrl.findingaids.forms import FindingAidForm
from cincoctrl.findingaids.forms import RevisionInlineFormSet
from cincoctrl.findingaids.forms import SubjectInlineFormSet
from cincoctrl.findingaids.forms import SuppFileInlineFormSet
from cincoctrl.findingaids.mixins import UserCanAccessRecordMixin
from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import Language
from cincoctrl.findingaids.parser import EADParser
from cincoctrl.users.mixins import UserHasAnyRoleMixin


class ManageRecordsView(UserHasAnyRoleMixin, ListView):
    model = FindingAid
    template_name = "findingaids/list_records.html"
    context_object_name = "records"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        default_page = 1
        page = self.request.GET.get("page", default_page)

        f = FindingAidFilter(
            self.request.GET,
            queryset=self.get_queryset(),
            repo_qs=self.request.user.repositories(),
        )

        items_per_page = 25
        paginator = Paginator(f.qs, items_per_page)

        try:
            records_page = paginator.page(page)
        except PageNotAnInteger:
            records_page = paginator.page(default_page)
        except EmptyPage:
            records_page = paginator.page(paginator.num_pages)

        context["filter"] = f
        context["records_page"] = records_page
        sep = "&" if len(self.request.GET) > 0 else "?"
        context["base_page_url"] = f"{self.request.get_full_path()}{sep}"
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(repository__in=self.request.user.repositories())


manage_records_view = ManageRecordsView.as_view()


class RecordDetailView(UserCanAccessRecordMixin, DetailView):
    model = FindingAid
    template_name = "findingaids/record.html"


view_record = RecordDetailView.as_view()


class EADMixin:
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["queryset"] = self.request.user.repositories()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verb"] = self.verb
        return context

    def extract_ead_fields(self, uploaded_file: InMemoryUploadedFile):
        file_content = b""
        for chunk in uploaded_file.chunks():
            file_content += chunk
        # reset file pointer for file save
        uploaded_file.seek(0)
        p = EADParser()
        p.parse_string(file_content, uploaded_file.name)
        return p.extract_ead_fields()

    def form_valid(self, form: ModelForm):
        if "ead_file" in self.request.FILES:
            (
                form.instance.collection_title,
                form.instance.collection_number,
                form.instance.ark,
            ) = self.extract_ead_fields(self.request.FILES["ead_file"])
        form.instance.queue_index()
        return super().form_valid(form)


class FindingAidCreateView(EADMixin, UserHasAnyRoleMixin, CreateView):
    model = FindingAid
    form_class = FindingAidForm
    template_name = "findingaids/form.html"
    verb = "Submit"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.record_type = "ead"
        return super().form_valid(form)


submit_ead = FindingAidCreateView.as_view()


class FindingAidUpdateView(EADMixin, UserCanAccessRecordMixin, UpdateView):
    model = FindingAid
    form_class = FindingAidForm
    template_name = "findingaids/form.html"
    verb = "Update"


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
            self.object.queue_index()
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


class RecordExpressXMLView(DetailView):
    model = ExpressRecord
    template_name = "findingaids/express_record.xml"

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Content-Disposition"] = 'attachment; filename="express_record.xml"'
        return response


view_record_express_xml = RecordExpressXMLView.as_view()


class PublishRecordView(UserCanAccessRecordMixin, DetailView):
    model = FindingAid
    template_name = "findingaids/queued.html"

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        obj.queue_index(force_publish=True)
        return obj


publish_record = PublishRecordView.as_view()


class PreviewRecordView(UserCanAccessRecordMixin, DetailView):
    model = FindingAid
    template_name = "findingaids/queued.html"

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        obj.queue_index()
        return obj


preview_record = PreviewRecordView.as_view()


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

        fa = form.instance
        if fa.ead_file.name:
            with fa.ead_file.open("rb") as x:
                content = x.read()
            parser = EADParser()
            parser.parse_string(content, fa.ead_file.name)
            parser.update_otherfindaids(
                [
                    {"url": f.pdf_file.url, "text": f.title}
                    for f in fa.supplementaryfile_set.all()
                ],
            )
            fa.ead_file = ContentFile(
                parser.to_string(),
                name=fa.ead_file.name,
            )
        fa.queue_index()
        return super().form_valid(form)


attach_pdf = AttachPDFView.as_view()


class LanguageAutocomplete(Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Language.objects.none()

        qs = Language.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


language_autocomplete = LanguageAutocomplete.as_view()
