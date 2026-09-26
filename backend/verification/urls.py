from django.urls import path

from .views import InventoryListCreateView, SpeakSwahiliView, VerifyMedicineView

urlpatterns = [
    path("verifications/", VerifyMedicineView.as_view(), name="verify-medicine"),
    path("verifications/<uuid:verification_id>/speak/", SpeakSwahiliView.as_view(), name="speak-swahili"),
    path("inventory/", InventoryListCreateView.as_view(), name="inventory-list-create"),
]
