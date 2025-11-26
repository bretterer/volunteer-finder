from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('create/', views.create_opportunity, name='create'),
    path('list/', views.list_opportunities, name='list'),
    path('<int:pk>/', views.opportunity_detail, name='detail'),
    path('<int:pk>/update-candidate/<int:score_id>/<str:status>/', views.update_candidate_status, name='update_candidate_status'),
    path('<int:pk>/apply/', views.apply_to_opportunity, name='apply_to_opportunity'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),

]
