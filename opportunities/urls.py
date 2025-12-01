from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('create/', views.create_opportunity, name='create'),
    path('list/', views.list_opportunities, name='list'),
    path('<int:pk>/', views.opportunity_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_opportunity, name='edit'),
    path('<int:pk>/update-candidate/<int:score_id>/<str:status>/', views.update_candidate_status, name='update_candidate_status'),
    path('<int:pk>/apply/', views.apply_to_opportunity, name='apply_to_opportunity'),
    path('<int:pk>/invite/<int:volunteer_id>/', views.invite_volunteer, name='invite_volunteer'),
    path('application/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('application/<int:application_id>/review/', views.review_application, name='review_application'),
]
