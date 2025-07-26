from django.urls import path
from .views import AgeGroupListCreateAPIView,AgeGroupRetrieveUpdateDestroyAPIView,TheoryListCreateAPIView,TheoryRetrieveUpdateDestroyAPIView,AssessmentListCreateView,AssessmentRetrieveUpdateDestroyAPIView,AIQuestionView

urlpatterns = [
    path('agegroup/',AgeGroupListCreateAPIView.as_view(),name="agegroup-list-create"),
    path('agegroup/<int:pk>/',AgeGroupRetrieveUpdateDestroyAPIView.as_view(),name="agegroup-retrieve-update-destroy"),
    path('theory/',TheoryListCreateAPIView.as_view(),name="theory-list-create"),
    path('theory/<int:pk>/',TheoryRetrieveUpdateDestroyAPIView.as_view(),name="theory-retrieve-update-destroy"),
    path('assessment/',AssessmentListCreateView.as_view(),name="assessment-list-create"),
    path('assessment/<int:pk>/',AssessmentRetrieveUpdateDestroyAPIView.as_view(),name="assessment-retrieve-update-destroy"),
    path("api/ai-assessment/<int:assessment_id>/", AIQuestionView.as_view(), name="ai-question"),


]