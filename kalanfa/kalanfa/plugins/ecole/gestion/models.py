"""
Modèles de gestion scolaire du plugin « ecole » — PROJET_SCHOOL_MOUMA_BKO_2026.

Chaque modèle est rattaché à une Facility (l'établissement = le tenant du
SaaS) : l'isolement des données entre écoles se fait par cette clé.

NOTE de conception : ces modèles sont des modèles Django ordinaires (non
synchronisés par morango). Dans un déploiement SaaS centralisé, la base est
unique côté serveur ; la synchronisation hors-ligne de ces données pourra
être ajoutée ultérieurement en les migrant vers AbstractFacilityDataModel.
"""
import uuid

from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models

from kalanfa.core.auth.models import Facility
from kalanfa.core.auth.models import FacilityUser


class UUIDPrimaryKeyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class EtablissementScopedModel(UUIDPrimaryKeyModel):
    """Base commune : rattachement au tenant + horodatage."""

    facility = models.ForeignKey(
        Facility, on_delete=models.CASCADE, related_name="+"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Sexe(models.TextChoices):
    MASCULIN = "M", "Masculin"
    FEMININ = "F", "Féminin"


class DossierEleve(EtablissementScopedModel):
    """Fiche de renseignement d'un élève."""

    eleve = models.OneToOneField(
        FacilityUser, on_delete=models.CASCADE, related_name="dossier_eleve"
    )
    sexe = models.CharField(max_length=1, choices=Sexe.choices, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=200, blank=True)
    nationalite = models.CharField(max_length=100, blank=True, default="Malienne")
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)

    # Scolarité antérieure et documents
    etablissement_precedent = models.CharField(max_length=200, blank=True)
    certificat_transfert = models.BooleanField(default=False)
    extrait_naissance_fourni = models.BooleanField(default=False)

    # Santé
    groupe_sanguin = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    contact_urgence_nom = models.CharField(max_length=200, blank=True)
    contact_urgence_telephone = models.CharField(max_length=30, blank=True)
    observations_medicales = models.TextField(blank=True)

    # Frais / bourse
    boursier = models.BooleanField(default=False)
    reduction_pourcentage = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(100)]
    )

    class Meta:
        verbose_name = "dossier élève"

    def __str__(self):
        return f"Dossier {self.eleve.username}"


class LienParente(models.TextChoices):
    PERE = "pere", "Père"
    MERE = "mere", "Mère"
    TUTEUR = "tuteur", "Tuteur / Tutrice"
    AUTRE = "autre", "Autre"


class Tuteur(EtablissementScopedModel):
    """Parent ou tuteur légal rattaché à un ou plusieurs dossiers."""

    nom_complet = models.CharField(max_length=200)
    lien = models.CharField(
        max_length=10, choices=LienParente.choices, default=LienParente.TUTEUR
    )
    profession = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)

    def __str__(self):
        return self.nom_complet


class DossierTuteur(UUIDPrimaryKeyModel):
    """
    Liaison dossier élève <-> tuteur.

    Jonction explicite (pas de ManyToManyField) : Kalanfa donne aux plugins
    un app_label pointé (« kalanfa.plugins.ecole ») que la machinerie des
    tables intermédiaires automatiques de Django ne sait pas résoudre.
    """

    dossier = models.ForeignKey(
        DossierEleve, on_delete=models.CASCADE, related_name="liens_tuteurs"
    )
    tuteur = models.ForeignKey(
        Tuteur, on_delete=models.CASCADE, related_name="liens_dossiers"
    )

    class Meta:
        unique_together = ("dossier", "tuteur")


class Periode(EtablissementScopedModel):
    """Période d'évaluation (ex. Trimestre 1 - 2026/2027)."""

    annee_scolaire = models.CharField(max_length=9)  # ex. "2026-2027"
    nom = models.CharField(max_length=50)  # ex. "Trimestre 1"
    ordre = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ("facility", "annee_scolaire", "nom")
        ordering = ["annee_scolaire", "ordre"]

    def __str__(self):
        return f"{self.nom} {self.annee_scolaire}"


class Note(EtablissementScopedModel):
    """Note d'un élève dans une matière, pour une période (sur 20)."""

    eleve = models.ForeignKey(
        FacilityUser, on_delete=models.CASCADE, related_name="notes_ecole"
    )
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE, related_name="notes")
    matiere = models.CharField(max_length=100)
    valeur = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
    )
    coefficient = models.PositiveSmallIntegerField(default=1)
    appreciation = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["matiere"]

    def __str__(self):
        return f"{self.eleve.username} - {self.matiere}: {self.valeur}/20"


class EcheanceFrais(EtablissementScopedModel):
    """Échéance de frais de scolarité pour un élève (montants en FCFA)."""

    eleve = models.ForeignKey(
        FacilityUser, on_delete=models.CASCADE, related_name="echeances_frais"
    )
    libelle = models.CharField(max_length=200)  # ex. "Scolarité Trimestre 1"
    montant_du = models.PositiveIntegerField()  # FCFA, pas de décimales
    date_echeance = models.DateField()

    class Meta:
        ordering = ["date_echeance"]

    @property
    def montant_paye(self):
        return sum(p.montant for p in self.paiements.all())

    @property
    def solde(self):
        return self.montant_du - self.montant_paye

    def __str__(self):
        return f"{self.libelle} — {self.eleve.username}"


class Paiement(EtablissementScopedModel):
    """Paiement (total ou partiel) d'une échéance ; sert de base au reçu."""

    echeance = models.ForeignKey(
        EcheanceFrais, on_delete=models.CASCADE, related_name="paiements"
    )
    montant = models.PositiveIntegerField()  # FCFA
    date_paiement = models.DateField()
    mode = models.CharField(max_length=50, blank=True)  # espèces, Orange Money...
    reference_recu = models.CharField(max_length=50, blank=True)
    encaisse_par = models.ForeignKey(
        FacilityUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        ordering = ["-date_paiement"]


class DomaineMontessori(models.TextChoices):
    VIE_PRATIQUE = "vie_pratique", "Vie pratique"
    SENSORIEL = "sensoriel", "Sensoriel"
    LANGAGE = "langage", "Langage"
    MATHEMATIQUES = "mathematiques", "Mathématiques"
    CULTURE = "culture", "Culture"


class NiveauAcquisition(models.TextChoices):
    PRESENTE = "presente", "Présenté"
    EN_COURS = "en_cours", "En cours d'acquisition"
    ACQUIS = "acquis", "Acquis"
    MAITRISE = "maitrise", "Maîtrisé"


class ObservationMontessori(EtablissementScopedModel):
    """Observation d'un enfant pendant le cycle de travail Montessori."""

    enfant = models.ForeignKey(
        FacilityUser, on_delete=models.CASCADE, related_name="observations_montessori"
    )
    educateur = models.ForeignKey(
        FacilityUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    date_observation = models.DateField()
    domaine = models.CharField(max_length=20, choices=DomaineMontessori.choices)
    activite = models.CharField(max_length=200)  # ex. "Tour rose", "Lettres rugueuses"
    niveau = models.CharField(
        max_length=10, choices=NiveauAcquisition.choices, default=NiveauAcquisition.PRESENTE
    )
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_observation"]

    def __str__(self):
        return f"{self.enfant.username} — {self.activite} ({self.get_niveau_display()})"


class FichePoste(EtablissementScopedModel):
    """Fiche de poste d'un membre du personnel."""

    titulaire = models.ForeignKey(
        FacilityUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fiches_poste",
    )
    intitule = models.CharField(max_length=200)  # ex. "Directeur pédagogique"
    missions = models.TextField(blank=True)
    responsabilites = models.TextField(blank=True)
    competences_requises = models.TextField(blank=True)

    class Meta:
        verbose_name = "fiche de poste"

    def __str__(self):
        return self.intitule
