from django.urls import include, path
from rest_framework import routers
from scoreboard import views
from rest_framework.routers import Route, DynamicRoute, SimpleRouter

router = routers.DefaultRouter()
router.register(r'games', views.GameViewSet)
router.register(r'ascended', views.AscendedViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [

    path('players/', views.PlayersList.as_view(), name='players-list'),
    path('players/<str:player>/', views.GamesByPlayerList.as_view()),
    path('players/<str:player>/ascended', views.AscensionsByPlayerList.as_view()),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
urlpatterns += router.urls