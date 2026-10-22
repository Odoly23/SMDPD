import datetime
from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from django.urls import reverse
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun
from config import roles
from config.user_utils import c_user_group, c_user_scope
from membro.models import Membro, Alokasaun, NIVEL, POZISAUN_POR_NIVEL, POZISAUN_BAIXA

BTN_CANCEL = """ <a class="btn btn-secondary" href="{{ cancel_url }}" title="Cancela"><i class="fa fa-close"></i> Cancela</a> """
BTN_SAVE = """ <button class="btn btn-primary" type="submit" title="Rai"> Rai <i class="fa fa-save"></i></button> """


def chain_attrs():
	"""URL AJAX ba dropdown berantai Munisipiu -> Postu -> Suku -> Aldeia."""
	return {
		'data-posts-url': reverse('ajax_load_posts'),
		'data-villages-url': reverse('ajax_load_villages'),
		'data-aldeias-url': reverse('ajax_load_aldeias'),
	}


class DateInput(forms.DateInput):
	input_type = 'date'

	def __init__(self, **kwargs):
		kwargs.setdefault('format', '%Y-%m-%d')
		super().__init__(**kwargs)


def normalize_eleitoral(value):
	return (value or '').strip().upper()


class ChainMixin:
	"""Limita opsaun postu/suku/aldeia tuir pai ne'ebé hili ona (atu la hatudu data barak liu)."""

	def _val(self, name):
		field = self.fields[name]
		if self.is_bound and not field.disabled:
			val = self.data.get(self.add_prefix(name))
		else:
			val = self.initial.get(name) or getattr(self.instance, f'{name}_id', None)
		return val if str(val).isdigit() else None

	def limit_chain(self):
		mun, post, village = self._val('municipality'), self._val('post'), self._val('village')
		self.fields['post'].queryset = AdministrativePost.objects.filter(municipality_id=mun) if mun else AdministrativePost.objects.none()
		self.fields['village'].queryset = Village.objects.filter(administrativepost_id=post) if post else Village.objects.none()
		self.fields['aldeia'].queryset = Aldeia.objects.filter(village_id=village) if village else Aldeia.objects.none()


class MembroForm(ChainMixin, forms.ModelForm):
	date_of_birth = forms.DateField(label="Data Moris", widget=DateInput(), required=True)
	data_hakbit = forms.DateField(label="Data Hakbit (Tama PLP)", widget=DateInput(), required=False)

	class Meta:
		model = Membro
		fields = ['nome', 'sex', 'place_of_birth', 'date_of_birth', 'marital', 'nu_eleitoral', 'nu_bi',
			'telefone', 'email', 'image', 'municipality', 'post', 'village', 'aldeia', 'address', 'organizasaun', 'data_hakbit', 'status',
			'nivel_edukasaun', 'area_estudu', 'servisu_fatin', 'municipality_orijin', 'esperensia', 'kontribuisaun']
		widgets = {'esperensia': forms.Textarea(attrs={'rows': 3}), 'kontribuisaun': forms.Textarea(attrs={'rows': 3})}

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)
		group = c_user_group(user) if user else None
		scope = c_user_scope(user) if user else None
		self.fields['organizasaun'].queryset = Organizasaun.objects.filter(is_active=True)
		self.fields['organizasaun'].empty_label = '--- Laiha ---'
		self.fields['municipality'].queryset = Municipality.objects.all()
		self.fields['municipality_orijin'].queryset = Municipality.objects.all()
		self.fields['municipality_orijin'].empty_label = '---------'
		self._terkunci(group, scope)
		self.limit_chain()
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_id = 'membroForm'
		self.helper.attrs = chain_attrs()
		self.helper.layout = Layout(
			Row(
				Column('nome', css_class='form-group col-md-6 mb-0'),
				Column('sex', css_class='form-group col-md-2 mb-0'),
				Column('nu_eleitoral', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('place_of_birth', css_class='form-group col-md-5 mb-0'),
				Column('date_of_birth', css_class='form-group col-md-3 mb-0'),
				Column('marital', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('nu_bi', css_class='form-group col-md-4 mb-0'),
				Column('telefone', css_class='form-group col-md-4 mb-0'),
				Column('image', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('municipality', css_class='form-group col-md-3 mb-0'),
				Column('post', css_class='form-group col-md-3 mb-0'),
				Column('village', css_class='form-group col-md-3 mb-0'),
				Column('aldeia', css_class='form-group col-md-3 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('address', css_class='form-group col-md-4 mb-0'),
				Column('organizasaun', css_class='form-group col-md-4 mb-0'),
				Column('data_hakbit', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('status', css_class='form-group col-md-4 mb-0'),
				Column('email', css_class='form-group col-md-8 mb-0'),
				css_class='form-row'
			),
			HTML('<h6 class="mt-3 text-primary text-uppercase"><i class="fa fa-graduation-cap"></i> Rekursu Intelektual</h6><hr class="mt-1">'),
			Row(
				Column('nivel_edukasaun', css_class='form-group col-md-3 mb-0'),
				Column('area_estudu', css_class='form-group col-md-5 mb-0'),
				Column('municipality_orijin', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('servisu_fatin', css_class='form-group col-md-12 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('esperensia', css_class='form-group col-md-6 mb-0'),
				Column('kontribuisaun', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			HTML(BTN_CANCEL),
			HTML(BTN_SAVE)
		)

	def _terkunci(self, group, scope):
		"""Koordenador input deit iha área rasik: field área kunci ho valór husi scope."""
		if not scope:
			return
		fixed = {}
		if group in roles.MUN_ROLES and scope.municipality_id:
			fixed = {'municipality': scope.municipality_id}
		elif group in roles.POSTU_ROLES and scope.post_id:
			fixed = {'municipality': scope.post.municipality_id, 'post': scope.post_id}
		elif group in roles.SUKU_ROLES and scope.village_id:
			v = scope.village
			fixed = {'municipality': v.administrativepost.municipality_id, 'post': v.administrativepost_id, 'village': v.pk}
		elif group in roles.ALDEIA_ROLES and scope.aldeia_id:
			a = scope.aldeia
			fixed = {'municipality': a.village.administrativepost.municipality_id, 'post': a.village.administrativepost_id,
				'village': a.village_id, 'aldeia': a.pk}
		elif group in roles.ORG_ROLES and scope.organizasaun_id:
			self.fields['organizasaun'].queryset = Organizasaun.objects.filter(pk=scope.organizasaun_id)
			self.fields['organizasaun'].empty_label = None
			self.fields['organizasaun'].initial = scope.organizasaun_id
			self.fields['organizasaun'].disabled = True
		for name, pk in fixed.items():
			self.initial[name] = pk
			self.fields[name].disabled = True

	def clean_nome(self):
		return ' '.join(self.cleaned_data['nome'].split())

	def clean_date_of_birth(self):
		dob = self.cleaned_data['date_of_birth']
		if dob > datetime.date.today():
			raise ValidationError('Data moris la bele iha futuru.')
		return dob

	def clean_nu_eleitoral(self):
		valor = normalize_eleitoral(self.cleaned_data['nu_eleitoral'])
		qs = Membro.objects.filter(nu_eleitoral__iexact=valor)
		if self.instance.pk:
			qs = qs.exclude(pk=self.instance.pk)
		dup = qs.select_related('village', 'aldeia').first()
		if dup:
			raise ValidationError(
				f'DUPLIKADU! Nu. Eleitoral {valor} registu ona ba {dup.nome} '
				f'iha Suku {dup.village}, Aldeia {dup.aldeia}. Ida ida deit bele rejistu.')
		return valor

	def clean(self):
		cleaned = super().clean()
		mun, post, village, aldeia = (cleaned.get(k) for k in ('municipality', 'post', 'village', 'aldeia'))
		if mun and post and post.municipality_id != mun.pk:
			self.add_error('post', 'Postu ne\'e la pertense ba munisipiu ne\'ebé hili.')
		if post and village and village.administrativepost_id != post.pk:
			self.add_error('village', 'Suku ne\'e la pertense ba postu ne\'ebé hili.')
		if village and aldeia and aldeia.village_id != village.pk:
			self.add_error('aldeia', 'Aldeia ne\'e la pertense ba suku ne\'ebé hili.')
		return cleaned


class RejeitaForm(forms.Form):
	razaun = forms.CharField(label="Razaun Rejeita", min_length=5, widget=forms.Textarea(attrs={'rows': 4}))

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.layout = Layout(
			'razaun',
			HTML(BTN_CANCEL),
			HTML(""" <button class="btn btn-danger" type="submit" title="Rejeita"> Rejeita <i class="fa fa-times"></i></button> """)
		)


class MembroChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		return f'{obj.nome} ({obj.nu_eleitoral or "-"}) - {obj.village or "-"}/{obj.aldeia or "-"}'


class AlokasaunForm(ChainMixin, forms.ModelForm):
	membro = MembroChoiceField(label="Membru", queryset=Membro.objects.none())
	data_hahu = forms.DateField(label="Data Hahu", widget=DateInput())
	data_termina = forms.DateField(label="Data Termina", widget=DateInput(), required=False)

	class Meta:
		model = Alokasaun
		fields = ['membro', 'nivel', 'pozisaun', 'departamentu', 'municipality', 'post', 'village', 'aldeia',
			'organizasaun', 'data_hahu', 'data_termina', 'ativu']

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.user = user
		self.group = c_user_group(user) if user else None
		layak = Membro.objects.filter(aprovasaun='Aprovadu', status='Ativu').select_related('village', 'aldeia')
		self._layak = layak
		pk = self.data.get(self.add_prefix('membro')) if self.is_bound else (self.instance.membro_id or None)
		self.fields['membro'].queryset = layak.filter(pk=pk) if str(pk).isdigit() else layak.none()
		self.fields['departamentu'].queryset = Departamentu.objects.filter(is_active=True)
		self.fields['organizasaun'].queryset = Organizasaun.objects.filter(is_active=True)
		self.fields['municipality'].queryset = Municipality.objects.all()
		self.fields['post'].required = False
		if self.group == roles.PRES_DEP:
			scope = c_user_scope(user)
			self.fields['nivel'].choices = [('Departamentu', 'Departamentu')]
			self.fields['nivel'].initial = 'Departamentu'
			self.fields['departamentu'].queryset = Departamentu.objects.filter(pk=scope.departamentu_id if scope else None)
			self.fields['departamentu'].initial = scope.departamentu_id if scope else None
			self.fields['departamentu'].empty_label = None
		if self.instance.pk and not self.is_bound:
			v = self.instance.village or (self.instance.aldeia.village if self.instance.aldeia_id else None)
			if v:
				self.initial.setdefault('village', v.pk)
				self.initial['post'] = v.administrativepost_id
				self.initial['municipality'] = v.administrativepost.municipality_id
		if self.group == roles.PRES_ORG:
			scope = c_user_scope(user)
			org_id = scope.organizasaun_id if scope else None
			self.fields['nivel'].choices = [('Organizasaun', 'Orgaun/Movimentu'), ('Departamentu', 'Departamentu')]
			self.fields['nivel'].initial = 'Organizasaun'
			self.fields['organizasaun'].queryset = Organizasaun.objects.filter(pk=org_id)
			self.fields['organizasaun'].initial = org_id
			self.fields['organizasaun'].empty_label = None
			self.fields['departamentu'].queryset = Departamentu.objects.filter(organizasaun_id=org_id, is_active=True)
			self._org_id = org_id
		self.limit_chain()
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_id = 'alokasaunForm'
		self.helper.attrs = {**chain_attrs(), 'data-membro-url': reverse('membro-search')}
		self.helper.layout = Layout(
			Row(
				Column(HTML('<label>Hetan membru (naran/nu. eleitoral)</label>'
					'<input type="text" id="cari-membro" class="form-control mb-1" placeholder="Hakerek naran ka nu. eleitoral..." autocomplete="off">'),
					'membro', css_class='form-group col-md-12 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('nivel', css_class='form-group col-md-6 mb-0'),
				Column('pozisaun', css_class='form-group col-md-6 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('departamentu', css_class='form-group col-md-12 mb-0 unit-departamentu'),
				css_class='form-row'
			),
			Row(
				Column('municipality', css_class='form-group col-md-3 mb-0 unit-munisipiu unit-postu unit-suku unit-aldeia unit-organizasaun'),
				Column('post', css_class='form-group col-md-3 mb-0 unit-postu unit-suku unit-aldeia'),
				Column('village', css_class='form-group col-md-3 mb-0 unit-suku unit-aldeia'),
				Column('aldeia', css_class='form-group col-md-3 mb-0 unit-aldeia'),
				css_class='form-row'
			),
			Row(
				Column('organizasaun', css_class='form-group col-md-12 mb-0 unit-organizasaun'),
				css_class='form-row'
			),
			Row(
				Column('data_hahu', css_class='form-group col-md-4 mb-0'),
				Column('data_termina', css_class='form-group col-md-4 mb-0'),
				Column('ativu', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			HTML(BTN_CANCEL),
			HTML(BTN_SAVE)
		)

	def clean(self):
		cleaned = super().clean()
		membro, nivel, pozisaun = cleaned.get('membro'), cleaned.get('nivel'), cleaned.get('pozisaun')
		if not (membro and nivel and pozisaun):
			return cleaned
		if pozisaun not in POZISAUN_POR_NIVEL[nivel]:
			self.add_error('pozisaun', f'Pozisaun {pozisaun} la existe iha nivel {nivel}.')
			return cleaned
		dep, mun, post = cleaned.get('departamentu'), cleaned.get('municipality'), cleaned.get('post')
		village, aldeia, org = cleaned.get('village'), cleaned.get('aldeia'), cleaned.get('organizasaun')
		unit = {'departamentu': None, 'municipality': None, 'post': None, 'village': None, 'aldeia': None, 'organizasaun': None}
		if nivel == 'Departamentu':
			if not dep:
				self.add_error('departamentu', 'Departamentu tenke hili.')
			unit['departamentu'] = dep
		elif nivel == 'Munisipiu':
			if not mun:
				self.add_error('municipality', 'Munisipiu tenke hili.')
			elif membro.municipality_id != mun.pk:
				self.add_error('membro', 'Membru ne\'e la hela iha munisipiu ne\'e.')
			unit['municipality'] = mun
		elif nivel == 'Postu':
			if not post:
				self.add_error('post', 'Postu Administrativu tenke hili.')
			elif membro.post_id != post.pk:
				self.add_error('membro', 'Membru ne\'e la hela iha postu ne\'e.')
			unit['post'] = post
		elif nivel == 'Suku':
			if not village:
				self.add_error('village', 'Suku tenke hili.')
			elif membro.village_id != village.pk:
				self.add_error('membro', 'Membru ne\'e la hela iha suku ne\'e.')
			unit['village'] = village
		elif nivel == 'Aldeia':
			if not aldeia:
				self.add_error('aldeia', 'Aldeia tenke hili.')
			elif membro.aldeia_id != aldeia.pk:
				self.add_error('membro', 'Membru ne\'e la hela iha aldeia ne\'e.')
			unit['aldeia'] = aldeia
		elif nivel == 'Organizasaun':
			unit['municipality'] = mun       # opsionál: filiál orgaun iha munisipiu (mamuk = nasionál)
			if not org:
				self.add_error('organizasaun', 'Orgaun/Movimentu tenke hili.')
			elif membro.organizasaun_id != org.pk:
				self.add_error('membro', 'Membru ne\'e la tama orgaun/movimentu ne\'e.')
			unit['organizasaun'] = org
		if self.group == roles.PRES_DEP and (nivel != 'Departamentu' or not unit['departamentu'] or unit['departamentu'].pk != self.fields['departamentu'].initial):
			raise ValidationError('Ita bele aloka deit iha departamentu rasik.')
		if self.group == roles.PRES_ORG:
			ok = (nivel == 'Organizasaun' and unit['organizasaun'] and unit['organizasaun'].pk == self._org_id) or \
				(nivel == 'Departamentu' and unit['departamentu'] and unit['departamentu'].organizasaun_id == self._org_id)
			if not ok:
				raise ValidationError('Ita bele aloka deit iha orgaun/movimentu rasik no nia departamentu.')
		if nivel == 'Departamentu' and unit['departamentu'] and unit['departamentu'].organizasaun_id \
				and membro.organizasaun_id != unit['departamentu'].organizasaun_id:
			self.add_error('membro', 'Departamentu ne\'e husi orgaun/movimentu, membru tenke tama orgaun/movimentu ne\'e.')
		cleaned.update(unit)
		if cleaned.get('data_termina') and cleaned.get('data_hahu') and cleaned['data_termina'] < cleaned['data_hahu']:
			self.add_error('data_termina', 'Data termina tenke depois data hahu.')
		if cleaned.get('ativu') == 'Sim' and not self.errors:
			qs = Alokasaun.objects.filter(nivel=nivel, ativu='Sim', **{k: v for k, v in unit.items()})
			if self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if pozisaun == POZISAUN_BAIXA:
				if qs.filter(pozisaun=pozisaun, membro=membro).exists():
					raise ValidationError(f'{membro.nome} iha ona hanesan {pozisaun} iha unidade ne\'e.')
			else:
				atual = qs.filter(pozisaun=pozisaun).select_related('membro').first()
				if atual:
					raise ValidationError(f'{pozisaun} {nivel} ativu iha ona: {atual.membro.nome}. Halo nia la ativu uluk.')
		return cleaned
