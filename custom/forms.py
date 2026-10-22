from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun

BTN_CANCEL = """ <a class="btn btn-secondary" href="{{ cancel_url }}" title="Cancela"><i class="fa fa-close"></i> Cancela</a> """
BTN_SAVE = """ <button class="btn btn-primary" type="submit" title="Rai"> Rai <i class="fa fa-save"></i></button> """


class MasterForm(forms.ModelForm):
	columns = []

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.layout = Layout(
			Row(*[Column(c, css_class='form-group col-md-4 mb-0') for c in self.columns], css_class='form-row'),
			HTML(BTN_CANCEL),
			HTML(BTN_SAVE)
		)

	def clean_name(self):
		return ' '.join(self.cleaned_data['name'].split())

	def _unik(self, model, name, **filtru):
		qs = model.objects.filter(name__iexact=name, **filtru)
		if self.instance.pk:
			qs = qs.exclude(pk=self.instance.pk)
		return qs.exists()


class MunicipalityForm(MasterForm):
	columns = ['code', 'name', 'hckey']

	class Meta:
		model = Municipality
		fields = ['code', 'name', 'hckey']

	def clean_name(self):
		name = super().clean_name()
		if self._unik(Municipality, name):
			raise forms.ValidationError('Munisipiu ho naran ne\'e iha ona.')
		return name


class PostForm(MasterForm):
	columns = ['municipality', 'name']

	class Meta:
		model = AdministrativePost
		fields = ['municipality', 'name']

	def clean(self):
		cleaned = super().clean()
		mun, name = cleaned.get('municipality'), cleaned.get('name')
		if mun and name and self._unik(AdministrativePost, name, municipality=mun):
			self.add_error('name', 'Postu ho naran ne\'e iha ona iha munisipiu ne\'e.')
		return cleaned


class VillageForm(MasterForm):
	columns = ['administrativepost', 'name']

	class Meta:
		model = Village
		fields = ['administrativepost', 'name']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['administrativepost'].queryset = AdministrativePost.objects.select_related('municipality')
		self.fields['administrativepost'].label_from_instance = lambda o: f'{o.municipality} / {o.name}'

	def clean(self):
		cleaned = super().clean()
		post, name = cleaned.get('administrativepost'), cleaned.get('name')
		if post and name and self._unik(Village, name, administrativepost=post):
			self.add_error('name', 'Suku ho naran ne\'e iha ona iha postu ne\'e.')
		return cleaned


class AldeiaForm(MasterForm):
	columns = ['village', 'name']

	class Meta:
		model = Aldeia
		fields = ['village', 'name']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['village'].queryset = Village.objects.select_related('administrativepost__municipality')
		self.fields['village'].label_from_instance = lambda o: f'{o.administrativepost.municipality} / {o.administrativepost} / {o.name}'

	def clean(self):
		cleaned = super().clean()
		village, name = cleaned.get('village'), cleaned.get('name')
		if village and name and self._unik(Aldeia, name, village=village):
			self.add_error('name', 'Aldeia ho naran ne\'e iha ona iha suku ne\'e.')
		return cleaned


class CodeNameForm(MasterForm):
	columns = ['code', 'name', 'is_active']

	def clean_code(self):
		code = self.cleaned_data['code'].strip().upper()
		qs = self._meta.model.objects.filter(code__iexact=code)
		if self.instance.pk:
			qs = qs.exclude(pk=self.instance.pk)
		if qs.exists():
			raise forms.ValidationError('Kódigu ne\'e iha ona.')
		return code


class DepartamentuForm(CodeNameForm):
	class Meta:
		model = Departamentu
		fields = ['code', 'name', 'is_active']


class OrganizasaunForm(CodeNameForm):
	columns = ['code', 'name', 'logo', 'is_active']

	class Meta:
		model = Organizasaun
		fields = ['code', 'name', 'logo', 'is_active']
