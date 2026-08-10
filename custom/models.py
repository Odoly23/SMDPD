from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class BaseModel(models.Model):
    created_by = models.ForeignKey(User,  on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created")
    created_at = models.DateTimeField(auto_now_add=True)
    # --------------------------------------------------------
    # AUDIT - UPDATED
    # --------------------------------------------------------
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,   related_name="%(class)s_updated")
    updated_at = models.DateTimeField(null=True, blank=True)
    # --------------------------------------------------------
    # AUDIT - DELETED
    # --------------------------------------------------------
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,    related_name="%(class)s_deleted")
    deleted_at = models.DateTimeField(null=True, blank=True)
    # --------------------------------------------------------
    # MANAGERS
    # --------------------------------------------------------
    objects = models.Manager()
    active_objects = ActiveManager()

    # --------------------------------------------------------
    # SOFT DELETE
    # --------------------------------------------------------
    def soft_delete(self, user=None):
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by"])

    # --------------------------------------------------------
    # RESTORE
    # --------------------------------------------------------
    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    class Meta:
        abstract = True


# ============================================================
# ENTIDADE
# ============================================================
class Entidade(BaseModel):
    code = models.CharField(max_length=10, unique=True, verbose_name="Kódigu")
    name = models.CharField(max_length=50, unique=True, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Entidade"
        verbose_name_plural = "Entidade Sira"
        ordering = ["name"]

# ============================================================
# ORGAUN
# ============================================================

class Orgaun(BaseModel):
    code = models.CharField(max_length=10, unique=True, verbose_name="Kódigu")
    name = models.CharField(max_length=100, unique=True, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Orgaun"
        verbose_name_plural = "Orgaun Sira"
        ordering = ["name"]
# ============================================================
# TERRITORY / MUNICIPALITY
# ============================================================
class Municipality(BaseModel):
    code = models.CharField(max_length=10, unique=True, verbose_name="Kódigu" )
    name = models.CharField(max_length=100,  unique=True, verbose_name="Naran")
    hckey = models.CharField(max_length=20,  null=True,  blank=True, verbose_name="HC Key")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Munisipiu"
        verbose_name_plural = "Munisipiu Sira"
        ordering = ["name"]


# ============================================================
# ADMINISTRATIVE POST
# ============================================================
class AdministrativePost(BaseModel):
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, related_name="administrative_posts",   verbose_name="Munisipiu")
    name = models.CharField(max_length=100,  verbose_name="Naran")

    def __str__(self):
        return (f"{self.name} - "f"{self.municipality.name}")

    class Meta:
        verbose_name = "Postu Administrativu"
        verbose_name_plural = "Postu Administrativu Sira"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "municipality",
                    "name"
                ],
                name="unique_post_per_municipality"
            )
        ]


# ============================================================
# VILLAGE / SUKU
# ============================================================

class Village(BaseModel):
    administrativepost = models.ForeignKey(AdministrativePost, on_delete=models.PROTECT, related_name="villages", verbose_name="Postu Administrativu")
    name = models.CharField(max_length=100, verbose_name="Naran")

    def __str__(self):
        return (f"{self.name} - "f"{self.administrativepost.name}")

    class Meta:
        verbose_name = "Suku"
        verbose_name_plural = "Suku Sira"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "administrativepost",
                    "name"
                ],
                name="unique_village_per_post"
            )
        ]


# ============================================================
# SUB VILLAGE / ALDEIA
# ============================================================
class SubVillage(BaseModel):
    village = models.ForeignKey(Village,  on_delete=models.PROTECT, related_name="subvillages", verbose_name="Suku")
    name = models.CharField(max_length=100,  verbose_name="Naran")

    def __str__(self):
        return (f"{self.name} - "f"{self.village.name}")

    class Meta:
        verbose_name = "Aldeia"
        verbose_name_plural = "Aldeia Sira"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "village",
                    "name"
                ],
                name="unique_subvillage_per_village"
            )
        ]


# ============================================================
# ESTRUCTURE
# ============================================================
class Estructure(BaseModel):
    code = models.CharField(max_length=20,  unique=True,  verbose_name="Kódigu")
    entidade = models.ForeignKey(Entidade, on_delete=models.PROTECT, related_name="estructures",  verbose_name="Entidade")
    orgaun = models.ForeignKey(Orgaun,  on_delete=models.PROTECT, related_name="estructures", verbose_name="Orgaun")
    municipality = models.ForeignKey(Municipality, on_delete=models.PROTECT, null=True, blank=True, related_name="estructures",  verbose_name="Munisipiu")
    administrativepost = models.ForeignKey( AdministrativePost, on_delete=models.PROTECT,   null=True, blank=True,  related_name="estructures",  verbose_name="Postu Administrativu")
    village = models.ForeignKey(Village, on_delete=models.PROTECT, null=True, blank=True, related_name="estructures", verbose_name="Suku")
    subvillage = models.ForeignKey(SubVillage, on_delete=models.PROTECT, null=True, blank=True, related_name="estructures", verbose_name="Aldeia")
    name = models.CharField(max_length=150, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Estrutura"
        verbose_name_plural = "Estrutura Sira"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "orgaun",
                    "entidade",
                    "name"
                ],
                name="unique_estrutura_orgao_entidade"
            )
        ]


# ============================================================
# CARGO
# ============================================================

class Cargo(BaseModel):
    code = models.CharField(max_length=20, unique=True, verbose_name="Kódigu")
    name = models.CharField(max_length=100, unique=True, verbose_name="Cargo")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargo Sira"
        ordering = ["name"]


# ============================================================
# POSITION / POSISAUN
# ============================================================

class Position(BaseModel):
    code = models.CharField(max_length=20, unique=True, verbose_name="Kódigu")
    entidade = models.ForeignKey(Entidade, on_delete=models.PROTECT, related_name="positions", verbose_name="Entidade")
    orgaun = models.ForeignKey(Orgaun, on_delete=models.PROTECT, related_name="positions", verbose_name="Orgaun")
    estructure = models.ForeignKey(Estructure, on_delete=models.PROTECT, related_name="positions", verbose_name="Estrutura")
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="positions", verbose_name="Cargo")
    name = models.CharField(max_length=150, verbose_name="Posisaun")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Posisaun"
        verbose_name_plural = "Posisaun Sira"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "estructure",
                    "cargo",
                    "name"
                ],
                name="unique_position_structure_cargo"
            )
        ]


# ============================================================
# EDUCATION LEVEL
# ============================================================

class EducationLevel(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Nivel Edukasaun"
        verbose_name_plural = "Nivel Edukasaun Sira"
        ordering = ["name"]


# ============================================================
# COUNTRY
# ============================================================

class Country(BaseModel):
    code = models.CharField(max_length=10, unique=True, verbose_name="Kódigu")
    name = models.CharField(max_length=100, unique=True, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Nasaun"
        verbose_name_plural = "Nasaun Sira"
        ordering = ["name"]


# ============================================================
# UNIVERSITY
# ============================================================

class University(BaseModel):
    country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True, blank=True, related_name="universities", verbose_name="Nasaun")
    name = models.CharField(max_length=150, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Universidade"
        verbose_name_plural = "Universidade Sira"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "country",
                    "name"
                ],
                name="unique_university_country"
            )
        ]


# ============================================================
# FACULTY
# ============================================================

class Faculty(BaseModel):
    university = models.ForeignKey(University, on_delete=models.PROTECT, null=True, blank=True, related_name="faculties", verbose_name="Universidade")
    name = models.CharField(max_length=150, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Faculdade"
        verbose_name_plural = "Faculdade Sira"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "university",
                    "name"
                ],
                name="unique_faculty_university"
            )
        ]


# ============================================================
# STUDY PROGRAM
# ============================================================

class StudyProgram(BaseModel):
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, null=True, blank=True, related_name="study_programs", verbose_name="Faculdade")
    name = models.CharField(max_length=150, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Programa Estudu"
        verbose_name_plural = "Programa Estudu Sira"
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "faculty",
                    "name"
                ],
                name="unique_study_program_faculty"
            )
        ]


# ============================================================
# AREA
# ============================================================

class Area(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="Naran")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Area Sira"
        ordering = ["name"]


# ============================================================
# YEAR
# ============================================================

class Year(BaseModel):
    year = models.IntegerField(unique=True, verbose_name="Tinan")
    is_active = models.BooleanField(default=False, verbose_name="Ativu")

    def __str__(self):
        return str(self.year)

    class Meta:
        verbose_name = "Tinan"
        verbose_name_plural = "Tinan Sira"
        ordering = ["-year"]


# ============================================================
# LANGUAGE
# ============================================================

class Language(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="Lingua")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Lingua"
        verbose_name_plural = "Lingua Sira"
        ordering = ["name"]


# ============================================================
# STATUS
# ============================================================

class Status(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="Status")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Status Sira"
        ordering = ["name"]