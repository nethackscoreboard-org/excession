from django.urls import include, path
from scoreboard import views

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('ascended', views.AscendedList.as_view(), name='ascended-list'),
    path('games', views.GamesList.as_view(), name='games-list'),
    path('leaderboards', views.LeaderboardsList.as_view(), name='leaderboards-list'),
    path('leaderboards/', views.NullView.as_view(), name='null-leaderboard'),
    path('leaderboards/realtime', views.RealtimeBoard.as_view(), name='realtime-leaderboard'),
    path('players', views.PlayersList.as_view(), name='players-list'),
    path('players/', views.NullPlayer.as_view(), name='null-player'),
    path('players/<str:player>', views.GamesByPlayerList.as_view(), name='games-by-player'),
    path('players/<str:player>/ascended', views.AscensionsByPlayerList.as_view(), name='wins-by-player'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', views.RootEndpointList.as_view(), name='root'),
]