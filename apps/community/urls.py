from django.urls import path

from apps.community import views

app_name = "community"

urlpatterns = [
    path("posts/", views.post_list, name="post_list"),
]