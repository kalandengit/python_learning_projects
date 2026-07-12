"""
Points d'accès REST du plugin ecole.

Isolement multi-tenant : chaque requête est filtrée sur la facility de
l'utilisateur connecté ; l'écriture est réservée aux admins/coachs de
l'établissement. Un utilisateur ne voit jamais les données d'une autre école.
"""
from django.db.models import Avg
from django.db.models import F
from django.db.models import Sum
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from kalanfa.core.auth.constants import role_kinds
from kalanfa.core.auth.models import FacilityUser

from .models import DossierEleve
from .models import EcheanceFrais
from .models import FichePoste
from .models import Note
from .models import ObservationMontessori
from .models import Paiement
from .models import Periode
from .models import Tuteur
from .serializers import DossierEleveSerializer
from .serializers import EcheanceFraisSerializer
from .serializers import FichePosteSerializer
from .serializers import NoteSerializer
from .serializers import ObservationMontessoriSerializer
from .serializers import PaiementSerializer
from .serializers import PeriodeSerializer
from .serializers import TuteurSerializer


def _user_facility(user):
    """Facility de rattachement de l'utilisateur (None pour anonyme)."""
    if not user or user.is_anonymous:
        return None
    return getattr(user, "facility", None)


def _is_staff_for_facility(user):
    """Admin d'établissement, coach, ou super-utilisateur du device."""
    if getattr(user, "is_superuser", False):
        return True
    facility = _user_facility(user)
    if facility is None:
        return False
    return user.has_role_for_collection(
        (role_kinds.ADMIN, role_kinds.COACH), facility
    )


class EstMembreEtablissement(permissions.BasePermission):
    """Lecture pour tout membre authentifié de l'école, écriture pour le staff."""

    def has_permission(self, request, view):
        user = request.user
        if not user or user.is_anonymous:
            return False
        if not isinstance(user, FacilityUser) and not getattr(
            user, "is_superuser", False
        ):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return _is_staff_for_facility(user)


class EcoleBaseViewSet(viewsets.ModelViewSet):
    """Base : filtre par facility du demandeur et assigne la facility en création."""

    permission_classes = (EstMembreEtablissement,)

    def get_queryset(self):
        facility = _user_facility(self.request.user)
        if facility is None:
            return self.queryset.none()
        return self.queryset.filter(facility=facility)

    def perform_create(self, serializer):
        serializer.save(facility=_user_facility(self.request.user))


class DossierEleveViewSet(EcoleBaseViewSet):
    queryset = DossierEleve.objects.all().select_related("eleve")
    serializer_class = DossierEleveSerializer


class TuteurViewSet(EcoleBaseViewSet):
    queryset = Tuteur.objects.all()
    serializer_class = TuteurSerializer


class PeriodeViewSet(EcoleBaseViewSet):
    queryset = Periode.objects.all()
    serializer_class = PeriodeSerializer


class NoteViewSet(EcoleBaseViewSet):
    queryset = Note.objects.all().select_related("eleve", "periode")
    serializer_class = NoteSerializer
    filterset_fields = ("eleve", "periode", "matiere")

    @action(detail=False, methods=["get"], url_path="bulletin")
    def bulletin(self, request):
        """
        Bulletin d'un élève pour une période : moyenne pondérée par matière,
        moyenne générale et rang dans l'établissement.

        Paramètres : ?eleve=<id>&periode=<id>
        """
        eleve_id = request.query_params.get("eleve")
        periode_id = request.query_params.get("periode")
        if not eleve_id or not periode_id:
            return Response(
                {"detail": "Paramètres requis : eleve, periode"}, status=400
            )
        base = self.get_queryset().filter(periode_id=periode_id)
        notes = base.filter(eleve_id=eleve_id)
        matieres = [
            {
                "matiere": n.matiere,
                "note": float(n.valeur),
                "coefficient": n.coefficient,
                "appreciation": n.appreciation,
            }
            for n in notes
        ]
        total_coef = sum(m["coefficient"] for m in matieres)
        moyenne = (
            round(
                sum(m["note"] * m["coefficient"] for m in matieres) / total_coef, 2
            )
            if total_coef
            else None
        )

        # Rang : moyenne pondérée de chaque élève de l'établissement sur la période
        moyennes = (
            base.values("eleve_id")
            .annotate(
                points=Sum(F("valeur") * F("coefficient")),
                coefs=Sum("coefficient"),
            )
            .annotate(moyenne=F("points") / F("coefs"))
            .order_by("-moyenne")
        )
        rang = None
        for i, row in enumerate(moyennes, start=1):
            if str(row["eleve_id"]) == str(eleve_id):
                rang = i
                break

        return Response(
            {
                "eleve": eleve_id,
                "periode": periode_id,
                "matieres": matieres,
                "moyenne_generale": moyenne,
                "rang": rang,
                "effectif": moyennes.count(),
            }
        )


class EcheanceFraisViewSet(EcoleBaseViewSet):
    queryset = EcheanceFrais.objects.all().prefetch_related("paiements")
    serializer_class = EcheanceFraisSerializer
    filterset_fields = ("eleve",)

    @action(detail=False, methods=["get"], url_path="impayes")
    def impayes(self, request):
        """Échéances dont le solde est positif (impayés), tous élèves confondus."""
        rows = []
        for echeance in self.get_queryset():
            solde = echeance.solde
            if solde > 0:
                rows.append(
                    {
                        "id": str(echeance.id),
                        "eleve": str(echeance.eleve_id),
                        "libelle": echeance.libelle,
                        "montant_du": echeance.montant_du,
                        "montant_paye": echeance.montant_paye,
                        "solde": solde,
                        "date_echeance": echeance.date_echeance,
                    }
                )
        return Response(rows)


class PaiementViewSet(EcoleBaseViewSet):
    queryset = Paiement.objects.all().select_related("echeance")
    serializer_class = PaiementSerializer


class ObservationMontessoriViewSet(EcoleBaseViewSet):
    queryset = ObservationMontessori.objects.all().select_related("enfant")
    serializer_class = ObservationMontessoriSerializer
    filterset_fields = ("enfant", "domaine", "niveau")

    @action(detail=False, methods=["get"], url_path="progression")
    def progression(self, request):
        """Synthèse par domaine pour un enfant : ?enfant=<id>."""
        enfant_id = request.query_params.get("enfant")
        if not enfant_id:
            return Response({"detail": "Paramètre requis : enfant"}, status=400)
        qs = self.get_queryset().filter(enfant_id=enfant_id)
        synthese = {}
        for obs in qs:
            domaine = synthese.setdefault(
                obs.domaine, {"total": 0, "acquis": 0, "activites": []}
            )
            domaine["total"] += 1
            if obs.niveau in ("acquis", "maitrise"):
                domaine["acquis"] += 1
            domaine["activites"].append(
                {
                    "activite": obs.activite,
                    "niveau": obs.niveau,
                    "date": obs.date_observation,
                }
            )
        return Response({"enfant": enfant_id, "domaines": synthese})


class FichePosteViewSet(EcoleBaseViewSet):
    queryset = FichePoste.objects.all().select_related("titulaire")
    serializer_class = FichePosteSerializer
