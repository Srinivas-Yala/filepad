from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.authenticate_user, name='authenticate'),
    path('files/', views.get_files, name='get_files'),
    path('upload/', views.upload_file, name='upload_file'),
    path('files/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('files/<int:file_id>/download/', views.download_file, name='download_file'),
]
