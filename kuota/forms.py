import datetime
from django import forms
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from config.user_utils import membro_scope
from kuota.models import Kuota
from membro.models import Membro

BTN_CANCEL = """ <a class="btn btn-secondary" href="{{ cancel_url }}" title="Cancela"><i class="fa fa-close"></i> Cancela</a> """
BTN_SAVE = """ <button class="btn btn-primary" type="submit" title="Rai"> Rai <i class="fa fa-save"></i></button> """


class DateInput(forms.DateInput):
	input_type = 'date'

	def __init__(self, **kwargs):
		kwargs.setdefault('format', '%Y-%m-%d')
		super().__init__(**kwargs)


class KuotaForm(forms.ModelForm):
	membro = forms.ModelChoiceField(label="Membru", queryset=Membro.objects.none())
	data_selu = forms.DateField(label="Data Selu", widget=DateInput(), initial=datetime.date.today)

	class Meta:
		model = Kuota
		fields = ['membro', 'tinan', 'montante', 'data_selu', 'metodu', 'nota']

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)
		layak = membro_scope(user).filter(aprovasaun='Aprovadu', status='Ativu') if user else Membro.objects.none()
		pk = self.data.get(self.add_prefix('membro')) if self.is_bound else None
		self.fields['membro'].queryset = layak.filter(pk=pk) if str(pk).isdigit() else layak.none()
		self.fields['membro'].label_from_instance = lambda o: f'{o.nome} ({o.nu_eleitoral or "-"})'
		self.fields['tinan'].initial = datetime.date.today().year
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_id = 'kuotaForm'
		self.helper.attrs = {'data-membro-url': reverse('kuota-search')}
		self.helper.layout = Layout(
			Row(Column(HTML('<label>Hetan membru (naran/nu. eleitoral)</label><input type="text" id="cari-membro" class="form-control mb-1" placeholder="Hakerek naran ka nu. eleitoral..." autocomplete="off">'),
				'membro', css_class='form-group col-md-12 mb-0'), css_class='form-row'),
			Row(Column('tinan', css_class='form-group col-md-3 mb-0'), Column('montante', css_class='form-group col-md-3 mb-0'),
				Column('data_selu', css_class='form-group col-md-3 mb-0'), Column('metodu', css_class='form-group col-md-3 mb-0'), css_class='form-row'),
			Row(Column('nota', css_class='form-group col-md-12 mb-0'), css_class='form-row'),
			HTML(BTN_CANCEL), HTML(BTN_SAVE))

	def clean_tinan(self):
		t = self.cleaned_data['tinan']
		if not 2000 <= t <= datetime.date.today().year + 1:
			raise forms.ValidationError('Tinan la loos.')
		return t
