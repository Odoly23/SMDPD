ADMIN = 'admin'
PRESIDENTE = 'presidente'
SEKRETARIA = 'sekretaria'
PRES_DEP = 'pres_dep'
KOORD_DEP = 'koord_dep'
KOORD_MUN = 'koord_mun'
KOORD_POSTU = 'koord_postu'
KOORD_SUKU = 'koord_suku'
KOORD_ALDEIA = 'koord_aldeia'
KOORD_ORG = 'koord_org'
PRES_ORG = 'pres_org'
VICE_ORG = 'vice_org'
SEKR_ORG = 'sekr_org'

ROLE_LABELS = [
	(PRESIDENTE, 'Presidente Nasionál'),
	(SEKRETARIA, 'Sekretaria Nasionál'),
	(PRES_DEP, 'Presidente Departamentu'),
	(KOORD_DEP, 'Koordenador Departamentu'),
	(KOORD_MUN, 'Koordenador Munisipal'),
	(KOORD_POSTU, 'Koordenador Postu Administrativu'),
	(KOORD_SUKU, 'Koordenador Suku'),
	(KOORD_ALDEIA, 'Koordenador Aldeia'),
	(PRES_ORG, 'Presidente Orgaun/Movimentu'),
	(VICE_ORG, 'Vice Orgaun/Movimentu'),
	(SEKR_ORG, 'Sekretaria Orgaun/Movimentu'),
	(KOORD_ORG, 'Koordenador Orgaun/Movimentu'),
	(ADMIN, 'Admin'),
]

NASIONAL_ROLES = [PRESIDENTE, SEKRETARIA]
DEP_ROLES = [PRES_DEP, KOORD_DEP]
MUN_ROLES = [KOORD_MUN]
POSTU_ROLES = [KOORD_POSTU]
SUKU_ROLES = [KOORD_SUKU]
ALDEIA_ROLES = [KOORD_ALDEIA]
ORG_ROLES = [PRES_ORG, VICE_ORG, SEKR_ORG, KOORD_ORG]

# Hak akses
VIEW_ROLES = NASIONAL_ROLES + DEP_ROLES + MUN_ROLES + POSTU_ROLES + SUKU_ROLES + ALDEIA_ROLES + ORG_ROLES
INPUT_ROLES = [SEKRETARIA, SEKR_ORG, KOORD_ORG] + MUN_ROLES + POSTU_ROLES + SUKU_ROLES + ALDEIA_ROLES  # input no edita data membru
APROVA_ROLES = [PRESIDENTE]                                                    # aprova, rejeita no hamoos membru
ALOKA_ROLES = [PRESIDENTE, SEKRETARIA, PRES_DEP, PRES_ORG]                               # aloka pozisaun iha struktura
HISTORIA_ROLES = [ADMIN, PRESIDENTE, SEKRETARIA]                               # lee historia mudansa data
