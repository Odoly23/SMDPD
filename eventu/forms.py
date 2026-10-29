from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from eventu.models import Eventu

BTN_CANCEL = """ <a class="btn btn-secondary" href="{{ cancel_url }}" title="Cancela"><i class="fa fa-close"></i> Cancela</a> """
BTN_SAVE = """ <button class="btn btn-primary" type="submit" title="Rai"> Rai <i class="fa fa-save"></i></button> """


class DateTimeInput(forms.DateTimeInput):
	input_type = 'datetime-local'

	def __init__(self, **kwargs):
		kwargs.setdefault('format', '%Y-%m-%dT%H:%M')
		super().__init__(**kwargs)


class EventuForm(forms.ModelForm):
	data_hahu = forms.DateTimeField(label="Data/Oras Hahu", widget=DateTimeInput(), input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'])
	data_remata = forms.DateTimeField(label="Data/Oras Remata", widget=DateTimeInput(), required=False, input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'])

	class Meta:
		model = Eventu
		fields = ['titulu', 'tipu', 'data_hahu', 'data_remata', 'fatin', 'deskrisaun']
		widgets = {'deskrisaun': forms.Textarea(attrs={'rows': 4})}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.layout = Layout(
			Row(Column('titulu', css_class='form-group col-md-8 mb-0'), Column('tipu', css_class='form-group col-md-4 mb-0'), css_class='form-row'),
			Row(Column('data_hahu', css_class='form-group col-md-4 mb-0'), Column('data_remata', css_class='form-group col-md-4 mb-0'),
				Column('fatin', css_class='form-group col-md-4 mb-0'), css_class='form-row'),
			Row(Column('deskrisaun', css_class='form-group col-md-12 mb-0'), css_class='form-row'),
			HTML(BTN_CANCEL), HTML(BTN_SAVE))

	def clean(self):
		cleaned = super().clean()
		a, b = cleaned.get('data_hahu'), cleaned.get('data_remata')
		if a and b and b < a:
			self.add_error('data_remata', 'Data remata tenke depois data hahu.')
		return cleaned
