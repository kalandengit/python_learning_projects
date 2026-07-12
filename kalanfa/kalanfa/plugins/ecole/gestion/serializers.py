"""Sérialiseurs DRF du plugin ecole."""
from rest_framework import serializers

from .models import DossierEleve
from .models import EcheanceFrais
from .models import FichePoste
from .models import Note
from .models import ObservationMontessori
from .models import Paiement
from .models import Periode
from .models import Tuteur


class DossierEleveSerializer(serializers.ModelSerializer):
    eleve_nom = serializers.CharField(source="eleve.full_name", read_only=True)

    class Meta:
        model = DossierEleve
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")


class TuteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tuteur
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")


class PeriodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Periode
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")


class EcheanceFraisSerializer(serializers.ModelSerializer):
    paiements = PaiementSerializer(many=True, read_only=True)
    montant_paye = serializers.IntegerField(read_only=True)
    solde = serializers.IntegerField(read_only=True)

    class Meta:
        model = EcheanceFrais
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")


class ObservationMontessoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservationMontessori
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")


class FichePosteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FichePoste
        exclude = ("facility",)
        read_only_fields = ("id", "date_creation", "date_modification")
