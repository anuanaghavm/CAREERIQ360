# from django.urls import path
# from .views import TestListCreateAPIView,TestRetrieveUpdateDestroyAPIView,TheoryListCreateAPIView,TheoryRetrieveUpdateDestroyAPIView,AgeGroupTestTheoryAPIView,AssessmentListCreateView,AssessmentRetrieveUpdateDestroyAPIView,AIQuestionView,AgeGroupReportAPIView,IndividualAssessmentReportAPIView

# urlpatterns = [
#     path('test/',TestListCreateAPIView.as_view(),name="agegroup-list-create"),
#     path('test/<int:pk>/',TestRetrieveUpdateDestroyAPIView.as_view(),name="agegroup-retrieve-update-destroy"),
#     path('theory/',TheoryListCreateAPIView.as_view(),name="theory-list-create"),
#     path('theory/<int:pk>/',TheoryRetrieveUpdateDestroyAPIView.as_view(),name="theory-retrieve-update-destroy"),
#     path('assessment/',AssessmentListCreateView.as_view(),name="assessment-list-create"),
#     path('assessment/<int:pk>/',AssessmentRetrieveUpdateDestroyAPIView.as_view(),name="assessment-retrieve-update-destroy"),
#     path('age-group/', AgeGroupTestTheoryAPIView.as_view(), name='age-group-tests-theories'),
#     path("ai-assessment/<int:assessment_id>/", AIQuestionView.as_view(), name="ai-question"),
#     path('ai-assessment/reports/', AgeGroupReportAPIView.as_view(), name='ai_report'),
#     path("assessment-report/<int:assessment_id>/", IndividualAssessmentReportAPIView.as_view(),name="assessment-report"),


# ]

from django.urls import path

from .views import StaticAIQuestionBatchView, StaticAIAnswerBatchView ,GenerateAssessmentReportView,GetSpecificReportView,GetUserReportsView,GetUserSessionsView

urlpatterns = [
    path('generate-questions/', StaticAIQuestionBatchView.as_view(), name='generate-questions'),
    path('submit-answers/', StaticAIAnswerBatchView.as_view(), name='submit-answers'),
    path("report/", GenerateAssessmentReportView.as_view()),
    path('user/<str:uuid>/reports/', GetUserReportsView.as_view(), name='get_user_reports'),
    path('report/<str:report_id>/', GetSpecificReportView.as_view(), name='get_specific_report'),
    path('user/<str:uuid>/sessions/', GetUserSessionsView.as_view(), name='get_user_sessions'),
]



