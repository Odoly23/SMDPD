from django.core.management import call_command
from django.test import TestCase
from custom.models import Municipality, AdministrativePost, Village, Aldeia


class ImportWilayahTests(TestCase):
	def jalan(self, *args):
		call_command('import_wilayah', *args, stdout=open('/dev/null', 'w'))

	def test_import_kompletu(self):
		self.jalan()
		self.assertEqual(Municipality.objects.count(), 14)
		self.assertEqual(AdministrativePost.objects.count(), 71)
		self.assertEqual(Village.objects.count(), 472)
		self.assertEqual(Aldeia.objects.count(), 2250)
		self.assertEqual(Municipality.objects.get(code='DIL').hckey, 'tl-dl')
		self.assertEqual(Municipality.objects.get(code='ATA').hckey, '')
		# ierarkia loos: aldeia -> suku -> postu -> munisipiu
		a = Aldeia.objects.select_related('village__administrativepost__municipality').get(code='AIL-A0001')
		self.assertEqual((a.name, a.village.code, a.village.administrativepost.code, a.village.administrativepost.municipality.code),
			('Aituhularan', 'AIL-S001', 'AIL-01', 'AIL'))

	def test_la_duplika_bainhira_la_o_dala_barak(self):
		self.jalan()
		self.jalan()
		self.assertEqual((Municipality.objects.count(), AdministrativePost.objects.count(), Village.objects.count(), Aldeia.objects.count()),
			(14, 71, 472, 2250))

	def test_munisipiu_antigu_uza_fali(self):
		antigu = Municipality.objects.create(name='Cova Lima', code='CL')
		oe = Municipality.objects.create(name='Oecusse', code='OE')
		self.jalan()
		self.assertEqual(Municipality.objects.count(), 14)
		antigu.refresh_from_db(); oe.refresh_from_db()
		self.assertEqual((antigu.code, antigu.name, antigu.hckey), ('COV', 'Covalima', 'tl-cl'))
		self.assertEqual((oe.code, oe.hckey), ('OEC', 'tl-am'))

	def test_dry_run_la_rai(self):
		self.jalan('--dry-run')
		self.assertEqual(Aldeia.objects.count(), 0)
