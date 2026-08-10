import hashlib
import uuid
from datetime import date

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

from custom.models import (
    BaseModel,
    Position,
    Country,
    Municipality,
    AdministrativePost,
    Status,
    Village,
    SubVillage,
    EducationLevel,
    University,
    Faculty,
    StudyProgram,
    Year,
    Area,
)

from config.upload_utills import (
    upload_photo,
    upload_estado,
    upload_formal,
)


# ============================================================
# MEMBRU
# ============================================================

class Membru(BaseModel):

    nu_id = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Nu. Eleitoral"
    )

    name = models.CharField(
        max_length=200,
        verbose_name="Naran"
    )

    pob = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Fatin Moris"
    )

    dob = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Moris"
    )

    sex = models.CharField(
        max_length=6,
        choices=[
            ("Mane", "Mane"),
            ("Feto", "Feto"),
        ],
        null=True,
        blank=True,
        verbose_name="Sexu"
    )

    marital = models.CharField(
        max_length=15,
        choices=[
            ("Solteiro/a", "Solteiro/a"),
            ("Casado/a", "Casado/a"),
            ("Divorciado/a", "Divorciado/a"),
            ("Viuvo/a", "Viuvo/a"),
        ],
        null=True,
        blank=True,
        verbose_name="Estado Civil"
    )

    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="membros",
        verbose_name="Status"
    )

    year = models.ForeignKey(
        Year,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="membros",
        verbose_name="Tinan"
    )

    file = models.FileField(
        upload_to=upload_estado,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ],
        verbose_name="Anexa Eleitoral"
    )

    hashed = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        editable=False
    )

    is_conf = models.BooleanField(
        default=False,
        verbose_name="Konfirmadu"
    )

    date_conf = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Konfirmasaun"
    )

    conf_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membros_confirmed",
        verbose_name="Konfirmadu Husi"
    )

    is_appr = models.BooleanField(
        default=False,
        verbose_name="Aprovadu"
    )

    date_appr = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Aprovasaun"
    )

    appr_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membros_approved",
        verbose_name="Aprovadu Husi"
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    def __str__(self):
        return self.name

    # --------------------------------------------------------
    # AGE
    # --------------------------------------------------------

    def age(self):
        if not self.dob:
            return None

        today = date.today()

        return (
            today.year
            - self.dob.year
            - (
                (today.month, today.day)
                < (self.dob.month, self.dob.day)
            )
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def clean(self):
        super().clean()

        if self.dob:
            umur = self.age()

            if umur is not None and umur < 16:
                raise ValidationError({
                    "dob": (
                        f"Idade tenke 16 anos ba leten. "
                        f"Idade agora: {umur} anos"
                    )
                })

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.hashed:

            self.hashed = hashlib.blake2b(
                f"{self.pk}-{uuid.uuid4()}".encode(),
                digest_size=64
            ).hexdigest()

            super().save(
                update_fields=["hashed"]
            )

    class Meta:
        verbose_name = "Membru"
        verbose_name_plural = "Membru Sira"
        ordering = ["name"]


# ============================================================
# CONTACT INFORMATION
# ============================================================

class ContactInfo(BaseModel):

    membro = models.OneToOneField(
        Membru,
        on_delete=models.CASCADE,
        related_name="contactinfo"
    )

    email = models.EmailField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Email"
    )

    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Nu. Telemovel"
    )

    hashed = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        editable=False
    )

    def __str__(self):
        return f"{self.membro} - {self.email or self.phone or ''}"

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.hashed:

            self.hashed = hashlib.blake2b(
                f"{self.pk}-{uuid.uuid4()}".encode(),
                digest_size=64
            ).hexdigest()

            super().save(
                update_fields=["hashed"]
            )

    class Meta:
        verbose_name = "Informasaun Kontaktu"
        verbose_name_plural = "Informasaun Kontaktu Sira"


# ============================================================
# LOCATION TIMOR-LESTE
# ============================================================

class LocationTL(BaseModel):

    membro = models.OneToOneField(
        Membru,
        on_delete=models.CASCADE,
        related_name="locationtl"
    )

    municipality = models.ForeignKey(
        Municipality,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="membro_locations",
        verbose_name="Munisipiu"
    )

    administrativepost = models.ForeignKey(
        AdministrativePost,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="membro_locations",
        verbose_name="Postu"
    )

    village = models.ForeignKey(
        Village,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="membro_locations",
        verbose_name="Suku"
    )

    aldeia = models.ForeignKey(
        SubVillage,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="membro_locations",
        verbose_name="Aldeia"
    )

    hashed = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        editable=False
    )

    # --------------------------------------------------------
    # VALIDATION WILAYAH
    # --------------------------------------------------------

    def clean(self):

        super().clean()

        if (
            self.administrativepost
            and self.municipality
            and self.administrativepost.municipality_id
            != self.municipality_id
        ):
            raise ValidationError({
                "administrativepost": (
                    "Postu Administrativu la pertense "
                    "ba Munisipiu ne'e."
                )
            })

        if (
            self.village
            and self.administrativepost
            and self.village.administrativepost_id
            != self.administrativepost_id
        ):
            raise ValidationError({
                "village": (
                    "Suku la pertense "
                    "ba Postu Administrativu ne'e."
                )
            })

        if (
            self.aldeia
            and self.village
            and self.aldeia.village_id
            != self.village_id
        ):
            raise ValidationError({
                "aldeia": (
                    "Aldeia la pertense "
                    "ba Suku ne'e."
                )
            })

    def __str__(self):
        if self.municipality:
            return f"{self.membro} - {self.municipality}"

        return str(self.membro)

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.hashed:

            self.hashed = hashlib.blake2b(
                f"{self.pk}-{uuid.uuid4()}".encode(),
                digest_size=64
            ).hexdigest()

            super().save(
                update_fields=["hashed"]
            )

    class Meta:
        verbose_name = "Localizasaun"
        verbose_name_plural = "Localizasaun Sira"


# ============================================================
# ADDRESS OF ORIGIN
# ============================================================

class AddressOrigin(BaseModel):

    membro = models.OneToOneField(
        Membru,
        on_delete=models.CASCADE,
        related_name="addressorigin"
    )

    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Cidade"
    )

    address = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="Enderesu"
    )

    def __str__(self):
        return f"{self.membro} - {self.city or ''}"

    class Meta:
        verbose_name = "Enderesu Orijen"
        verbose_name_plural = "Enderesu Orijen Sira"


# ============================================================
# PHOTO
# ============================================================

class Photo(BaseModel):

    membro = models.OneToOneField(
        Membru,
        on_delete=models.CASCADE,
        related_name="photo"
    )

    image = models.ImageField(
        upload_to=upload_photo,
        default="default.png",
        null=True,
        blank=True,
        verbose_name="Foto"
    )

    def __str__(self):
        return str(self.membro)

    class Meta:
        verbose_name = "Foto"
        verbose_name_plural = "Foto Sira"


# ============================================================
# FORMAL EDUCATION
# ============================================================

class FormalEducation(BaseModel):

    membro = models.ForeignKey(
        Membru,
        on_delete=models.CASCADE,
        related_name="formal_educations"
    )

    educationlevel = models.ForeignKey(
        EducationLevel,
        on_delete=models.PROTECT,
        related_name="formal_educations",
        verbose_name="Nivel Edukasaun"
    )

    university = models.ForeignKey(
        University,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="formal_educations",
        verbose_name="Universidade"
    )

    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="formal_educations",
        verbose_name="Faculdade"
    )

    studyprogram = models.ForeignKey(
        StudyProgram,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="formal_educations",
        verbose_name="Programa Estudu"
    )

    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="formal_educations",
        verbose_name="Area Professional"
    )

    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tinan Gradua"
    )

    summary = models.TextField(
        null=True,
        blank=True,
        verbose_name="Sumariu"
    )

    file = models.FileField(
        upload_to=upload_formal,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ],
        verbose_name="Anexu Certifikadu"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativu"
    )

    hashed = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        editable=False
    )

    def __str__(self):
        return (
            f"{self.membro} - "
            f"{self.educationlevel}"
        )

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.hashed:

            self.hashed = hashlib.blake2b(
                f"{self.pk}-{uuid.uuid4()}".encode(),
                digest_size=64
            ).hexdigest()

            super().save(
                update_fields=["hashed"]
            )

    class Meta:
        verbose_name = "Edukasaun Formal"
        verbose_name_plural = "Edukasaun Formal Sira"
        ordering = ["-graduation_year"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "membro",
                    "educationlevel",
                    "university",
                    "studyprogram"
                ],
                name="unique_member_education"
            )
        ]


# ============================================================
# MEMBER USER
# ============================================================

class MembroUser(BaseModel):

    membro = models.OneToOneField(
        Membru,
        on_delete=models.CASCADE,
        related_name="membrouser"
    )

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membro_profile"
    )

    def __str__(self):
        return (
            f"{self.membro} - "
            f"{self.user.username if self.user else ''}"
        )

    class Meta:
        verbose_name = "Membro User"
        verbose_name_plural = "Membro User Sira"


# ============================================================
# MEMBER POSITION / RIWAYAT JABATAN
# ============================================================

class MembroPosition(BaseModel):

    membro = models.ForeignKey(
        Membru,
        on_delete=models.CASCADE,
        related_name="member_positions"
    )

    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="member_positions",
        verbose_name="Posisaun"
    )

    start_date = models.DateField(
        verbose_name="Data Hahu"
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Remata"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativu"
    )

    sk_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Nu. SK"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def clean(self):

        super().clean()

        if (
            self.end_date
            and self.start_date
            and self.end_date < self.start_date
        ):
            raise ValidationError({
                "end_date": (
                    "Data remata la bele menus "
                    "husi data hahu."
                )
            })

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    def __str__(self):

        if self.position:
            return (
                f"{self.membro.name} - "
                f"{self.position.name}"
            )

        return self.membro.name

    class Meta:
        verbose_name = "Pozisaun Membro"
        verbose_name_plural = "Pozisaun Membro Sira"
        ordering = [
            "-is_active",
            "-start_date"
        ]

