ADMIN = 'admin'
PRESIDENTE = 'presidente'
SEKRETARIA = 'sekretaria'
PRES_DEP = 'pres_dep'
KOORD_DEP = 'koord_dep'
KOORD_MUN = 'koord_mun'
KOORD_SUKU = 'koord_suku'
KOORD_ALDEIA = 'koord_aldeia'
KOORD_ORG = 'koord_org'

ROLE_LABELS = [
	(PRESIDENTE, 'Presidente Nasionál'),
	(SEKRETARIA, 'Sekretaria Nasionál'),
	(PRES_DEP, 'Presidente Departamentu'),
	(KOORD_DEP, 'Koordenador Departamentu'),
	(KOORD_MUN, 'Koordenador Munisipiu'),
	(KOORD_SUKU, 'Koordenador Suku'),
	(KOORD_ALDEIA, 'Koordenador Aldeia'),
	(KOORD_ORG, 'Koordenador Organizasaun'),
	(ADMIN, 'Admin'),
]

NASIONAL_ROLES = [PRESIDENTE, SEKRETARIA]
DEP_ROLES = [PRES_DEP, KOORD_DEP]
MUN_ROLES = [KOORD_MUN]
SUKU_ROLES = [KOORD_SUKU]
ALDEIA_ROLES = [KOORD_ALDEIA]
ORG_ROLES = [KOORD_ORG]

# Hak akses
VIEW_ROLES = NASIONAL_ROLES + DEP_ROLES + MUN_ROLES + SUKU_ROLES + ALDEIA_ROLES + ORG_ROLES
INPUT_ROLES = [SEKRETARIA] + MUN_ROLES + SUKU_ROLES + ALDEIA_ROLES + ORG_ROLES  # input no edita data membru
APROVA_ROLES = [PRESIDENTE]                                                    # aprova, rejeita no hamoos membru
ALOKA_ROLES = [PRESIDENTE, SEKRETARIA, PRES_DEP]                               # aloka pozisaun iha struktura
HISTORIA_ROLES = [ADMIN, PRESIDENTE, SEKRETARIA]                               # lee historia mudansa data
