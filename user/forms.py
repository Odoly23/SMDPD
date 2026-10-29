from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML
from config import roles
from config.user_utils import c_user_group, c_user_scope
from custom.models import Municipality, AdministrativePost, Village, Aldeia, Departamentu, Organizasaun
from user.models import UserScope

BTN_CANCEL = """ <a class="btn btn-secondary" href="{{ cancel_url }}" title="Cancela"><i class="fa fa-close"></i> Cancela</a> """
BTN_SAVE = """ <button class="btn btn-primary" type="submit" title="Rai"> Rai <i class="fa fa-save"></i></button> """


class UserForm(forms.ModelForm):
	group = forms.ChoiceField(label="Peran", choices=roles.ROLE_LABELS)
	departamentu = forms.ModelChoiceField(label="Departamentu", queryset=Departamentu.objects.filter(is_active=True), required=False)
	municipality = forms.ModelChoiceField(label="Munisipal", queryset=Municipality.objects.all(), required=False)
	post = forms.ModelChoiceField(label="Postu Administrativu", queryset=AdministrativePost.objects.select_related('municipality'), required=False)
	village = forms.ModelChoiceField(label="Suku", queryset=Village.objects.select_related('administrativepost'), required=False)
	aldeia = forms.ModelChoiceField(label="Aldeia", queryset=Aldeia.objects.select_related('village'), required=False)
	organizasaun = forms.ModelChoiceField(label="Orgaun/Movimentu", queryset=Organizasaun.objects.filter(is_active=True), required=False)
	password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}), required=False)

	class Meta:
		model = User
		fields = ['username', 'first_name', 'email', 'is_active']
		labels = {'username': 'Username', 'first_name': 'Naran Kompletu', 'email': 'Email', 'is_active': 'Ativu'}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['first_name'].required = True
		self.fields['village'].label_from_instance = lambda o: f'{o.administrativepost} / {o.name}'
		self.fields['aldeia'].label_from_instance = lambda o: f'{o.village} / {o.name}'
		if self.instance.pk:
			self.fields['group'].initial = c_user_group(self.instance)
			scope = c_user_scope(self.instance)
			if scope:
				for k in ('departamentu', 'municipality', 'post', 'village', 'aldeia', 'organizasaun'):
					self.fields[k].initial = getattr(scope, f'{k}_id')
			self.fields['password'].help_text = 'Husik mamuk atu la troka.'
		else:
			self.fields['password'].required = True
			self.fields['is_active'].initial = True
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_id = 'userForm'
		self.helper.layout = Layout(
			Row(
				Column('username', css_class='form-group col-md-4 mb-0'),
				Column('first_name', css_class='form-group col-md-4 mb-0'),
				Column('email', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('group', css_class='form-group col-md-4 mb-0'),
				Column('password', css_class='form-group col-md-4 mb-0'),
				Column('is_active', css_class='form-group col-md-4 mb-0'),
				css_class='form-row'
			),
			Row(
				Column('departamentu', css_class='form-group col-md-4 mb-0 scope-departamentu'),
				Column('municipality', css_class='form-group col-md-4 mb-0 scope-municipality'),
				Column('post', css_class='form-group col-md-4 mb-0 scope-post'),
				css_class='form-row'
			),
			Row(
				Column('village', css_class='form-group col-md-4 mb-0 scope-village'),
				Column('aldeia', css_class='form-group col-md-4 mb-0 scope-aldeia'),
				Column('organizasaun', css_class='form-group col-md-4 mb-0 scope-organizasaun'),
				css_class='form-row'
			),
			HTML(BTN_CANCEL),
			HTML(BTN_SAVE)
		)

	def clean(self):
		cleaned = super().clean()
		group = cleaned.get('group')
		scope = {k: cleaned.get(k) for k in ('departamentu', 'municipality', 'post', 'village', 'aldeia', 'organizasaun')}
		keep, label = None, ''
		if group in roles.DEP_ROLES:
			keep, label = 'departamentu', 'Departamentu'
		elif group in roles.MUN_ROLES:
			keep, label = 'municipality', 'Munisipal'
		elif group in roles.POSTU_ROLES:
			keep, label = 'post', 'Postu Administrativu'
		elif group in roles.SUKU_ROLES:
			keep, label = 'village', 'Suku'
		elif group in roles.ALDEIA_ROLES:
			keep, label = 'aldeia', 'Aldeia'
		elif group in roles.ORG_ROLES:
			keep, label = 'organizasaun', 'Orgaun/Movimentu'
		if keep and not scope[keep]:
			self.add_error(keep, f'{label} tenke hili ba peran ida ne\'e.')
		for k in scope:
			if k != keep:
				scope[k] = None
		cleaned.update(scope)
		password = cleaned.get('password')
		if password:
			try:
				validate_password(password, user=self.instance if self.instance.pk else User(username=cleaned.get('username', '')))
			except forms.ValidationError as e:
				self.add_error('password', e)
		return cleaned

	def save(self, commit=True):
		user = super().save(commit=False)
		if self.cleaned_data.get('password'):
			user.set_password(self.cleaned_data['password'])
		user.save()
		group, _ = Group.objects.get_or_create(name=self.cleaned_data['group'])
		user.groups.set([group])
		defaults = {k: self.cleaned_data[k] for k in ('departamentu', 'municipality', 'post', 'village', 'aldeia', 'organizasaun')}
		if self.cleaned_data.get('password'):
			defaults['troka_password'] = True      # password husi Admin: uzuáriu tenke troka bainhira login
		UserScope.objects.update_or_create(user=user, defaults=defaults)
		return user
