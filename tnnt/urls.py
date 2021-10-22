from django.urls import include, path
from scoreboard import views
from tnnt import views as tnntviews

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', tnntviews.HomepageView.as_view(), name='root'),
    path('leaderboards', tnntviews.LeaderboardsView.as_view(), name='leaderboards'),
    # TODO path('clans', tnntviews.ClansView.as_view(), name='clans'),
    path('players', tnntviews.PlayersView.as_view(), name='players'),
    path('player/<str:playername>', tnntviews.SinglePlayerView.as_view(), name='singleplayer'),
    # TODO path('clan/<str:clanname>', tnntviews.SingleClanView.as_view(), name='singleclan'),
    path('rules', tnntviews.RulesView.as_view(), name='rules'),
    path('about', tnntviews.AboutView.as_view(), name='about'),
    path('archives', tnntviews.ArchivesView.as_view(), name='archives'),
    path('clanmgmt', tnntviews.ClanMgmtView.as_view(), name='clanmgmt'),
    path('', include('django.contrib.auth.urls')),
]

