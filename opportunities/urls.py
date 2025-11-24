from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('create/', views.create_opportunity, name='create'),
    path('list/', views.list_opportunities, name='list'),
    path('<int:pk>/', views.opportunity_detail, name='detail'),
    path('<int:pk>/update-candidate/<int:score_id>/<str:status>/', views.update_candidate_status, name='update_candidate_status')
]
