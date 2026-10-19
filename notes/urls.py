from django.urls import path

from . import views

urlpatterns = [
    path("", views.public_feed, name="public_feed"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("my/", views.my_notes, name="my_notes"),
    path("note/new/", views.create_note, name="create_note"),
    path("note/<int:note_id>/", views.note_detail, name="note_detail"),
    path("note/<int:note_id>/edit/", views.edit_note, name="edit_note"),
    path("search/", views.search_notes, name="search_notes"),
    path("moderation/", views.moderation, name="moderation"),
]
