from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from config import roles
from config.user_utils import c_user_group, c_user_unit
from custom.models import Municipality, Departamentu, Organizasaun
from anunsiu.models import Anunsiu, AUDIENS

BTN_CANCEL = """ <a class="btn btn-secondary" href="{{ cancel_url }}" title="Cancela"><i class="fa fa-close"></i> Cancela</a> """
BTN_SAVE = """ <button class="btn btn-primary" type="submit" title="Rai"> Rai <i class="fa fa-save"></i></button> """


class DateInput(forms.DateInput):
	input_type = 'date'

	def __init__(self, **kwargs):
		kwargs.setdefault('format', '%Y-%m-%d')
		super().__init__(**kwargs)


class AnunsiuForm(forms.ModelForm):
	data_remata = forms.DateField(label="Validu to'o", widget=DateInput(), required=False)

	class Meta:
		model = Anunsiu
		fields = ['titulu', 'mensagem', 'audiens', 'municipality', 'organizasaun', 'departamentu', 'importante', 'data_remata']
		widgets = {'mensagem': forms.Textarea(attrs={'rows': 6})}

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.group = c_user_group(user) if user else None
		u = c_user_unit(user) if user else {}
		self.fields['municipality'].queryset = Municipality.objects.all()
		self.fields['organizasaun'].queryset = Organizasaun.objects.filter(is_active=True)
		self.fields['departamentu'].queryset = Departamentu.objects.filter(is_active=True)
		self.fixa = None
		if self.group == roles.PRES_ORG:
			self.fixa = ('Organizasaun', 'organizasaun', u.get('organizasaun'))
		elif self.group == roles.PRES_DEP:
			self.fixa = ('Departamentu', 'departamentu', u.get('departamentu'))
		elif self.group == roles.KOORD_MUN:
			self.fixa = ('Munisipiu', 'municipality', u.get('municipality'))
		if self.fixa:
			nivel, campo, obj = self.fixa
			self.fields['audiens'].choices = [c for c in AUDIENS if c[0] == nivel]
			self.fields['audiens'].initial = nivel
			self.fields[campo].queryset = self.fields[campo].queryset.filter(pk=obj.pk if obj else None)
			self.fields[campo].initial = obj.pk if obj else None
			self.fields[campo].empty_label = None
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_id = 'anunsiuForm'
		self.helper.layout = Layout(
			Row(Column('titulu', css_class='form-group col-md-12 mb-0'), css_class='form-row'),
			Row(Column('mensagem', css_class='form-group col-md-12 mb-0'), css_class='form-row'),
			Row(
				Column('audiens', css_class='form-group col-md-3 mb-0'),
				Column('municipality', css_class='form-group col-md-3 mb-0 alvu-munisipiu'),
				Column('organizasaun', css_class='form-group col-md-3 mb-0 alvu-organizasaun'),
				Column('departamentu', css_class='form-group col-md-3 mb-0 alvu-departamentu'),
				css_class='form-row'
			),
			Row(
				Column('data_remata', css_class='form-group col-md-4 mb-0'),
				Column('importante', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			HTML(BTN_CANCEL),
			HTML(BTN_SAVE)
		)

	def clean(self):
		cleaned = super().clean()
		aud = cleaned.get('audiens')
		campos = {'Munisipiu': 'municipality', 'Organizasaun': 'organizasaun', 'Departamentu': 'departamentu'}
		if aud in campos and not cleaned.get(campos[aud]):
			self.add_error(campos[aud], 'Tenke hili ba audiens ne\'e.')
		for k, c in campos.items():
			if k != aud:
				cleaned[c] = None
		if self.fixa and aud != self.fixa[0]:
			raise forms.ValidationError('Ita bele hatama anunsiu deit ba ita nia unidade rasik.')
		return cleaned
