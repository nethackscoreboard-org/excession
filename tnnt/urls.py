from django.urls import include, path
from scoreboard import views

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('ascended', views.AscendedList.as_view(), name='ascended-list'),
    path('games', views.GamesList.as_view(), name='games-list'),
    path('leaderboards', views.LeaderboardsList.as_view(), name='leaderboards-list'),
    path('leaderboards/conducts', views.ConductsBoard.as_view(), name='conducts-leaderboard'),
    path('leaderboards/minscore', views.MinscoreBoard.as_view(), name='minscore-leaderboard'),
    path('leaderboards/realtime', views.RealtimeBoard.as_view(), name='realtime-leaderboard'),
    path('leaderboards/turncount', views.TurncountBoard.as_view(), name='turncount-leaderboard'),
    path('leaderboards/wallclock', views.WallclockBoard.as_view(), name='wallclock-leaderboard'),
    path('players', views.PlayersList.as_view(), name='players-list'),
    path('players/<str:player>', views.GamesList.as_view(), name='games-by-player'),
    path('players/<str:player>/ascended', views.AscendedList.as_view(), name='wins-by-player'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', views.RootEndpointList.as_view(), name='root'),
]