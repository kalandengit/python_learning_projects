"""Routage API du plugin ecole (préfixé par le slug du plugin)."""
from rest_framework import routers

from .gestion.viewsets import DossierEleveViewSet
from .gestion.viewsets import EcheanceFraisViewSet
from .gestion.viewsets import FichePosteViewSet
from .gestion.viewsets import NoteViewSet
from .gestion.viewsets import ObservationMontessoriViewSet
from .gestion.viewsets import PaiementViewSet
from .gestion.viewsets import PeriodeViewSet
from .gestion.viewsets import TuteurViewSet

router = routers.SimpleRouter()
router.register("dossiers", DossierEleveViewSet, basename="dossiereleve")
router.register("tuteurs", TuteurViewSet, basename="tuteur")
router.register("periodes", PeriodeViewSet, basename="periode")
router.register("notes", NoteViewSet, basename="note")
router.register("frais", EcheanceFraisViewSet, basename="echeancefrais")
router.register("paiements", PaiementViewSet, basename="paiement")
router.register(
    "observations", ObservationMontessoriViewSet, basename="observationmontessori"
)
router.register("fiches-poste", FichePosteViewSet, basename="ficheposte")

urlpatterns = router.urls
