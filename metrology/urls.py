from rest_framework.routers import DefaultRouter

from .views import InstrumentViewSet, VerificationViewSet


router = DefaultRouter()
router.register("instruments", InstrumentViewSet, basename="instrument")
router.register("verifications", VerificationViewSet, basename="verification")

urlpatterns = router.urls