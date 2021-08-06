from django.urls import include, path
from rest_framework import routers
from scoreboard import views
from rest_framework.routers import Route, DynamicRoute, SimpleRouter

router = routers.DefaultRouter()
router.register(r'games', views.GameViewSet)
router.register(r'ascended', views.AscendedViewSet)
router.register(r'players', views.PlayerViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('rs/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
