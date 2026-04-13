from django.urls import path
from . import views

app_name = "auth0"

urlpatterns =[
    path('login/android', view=views.login_view_android, name="login_android"),
    path('login/web', view=views.login_web, name="login_web"),
    path('register', view=views.register, name="register"),
    path('logout/web', view=views.logout_view, name="logout_web")
]