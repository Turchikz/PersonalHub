from rest_framework.routers import DefaultRouter

from .views import InstrumentViewSet


router = DefaultRouter()
router.register("instruments", InstrumentViewSet, basename="instrument")

urlpatterns = router.urls