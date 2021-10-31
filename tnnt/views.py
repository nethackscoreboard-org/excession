from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.db.models import Exists, OuterRef, F, Count, Value, Sum
from scoreboard.models import *
from tnnt.forms import CreateClanForm, InviteMemberForm
from django.http import HttpResponse, HttpResponseRedirect
from . import hardfought_utils # find_player
from . import dumplog_utils # format_dumplog
from . import settings
from datetime import datetime, timezone
import logging
from django.db import connection # TODO: for debugging only
from tnnt import uniqdeaths

logger = logging.getLogger() # use root logger

# Convenience function, not a view.
# Given a list of dicts containing Game fields (specifically 'playername',
# 'dlg_fmt' and 'starttime'), also insert a 'dumplog' field into each of those
# dicts containing the formatted dumplog URL.
def bulk_upd_games(gamelist):
    for g in gamelist:
        g['dumplog'] = dumplog_utils.format_dumplog(g['dlg_fmt'], g['playername'],
                                                    g['starttime'])

        # post 2021 TODO: this is a duplicate of Game.rrga, but unlike dumplog
        # formatting, that function is used in aggregation
        g['rrga'] = '-'.join([g['role'], g['race'], g['gender0'], g['align0']])

        # TODO: this is not ideal because it's an extra query per each ascension
        # in the list. but perhaps not worth the headache of making all these
        # preproc'd Game lists into Game-x-Conduct lists.
        # This used to be Game.conducts_as_str, whose description was:
        # > Return a string containing this game's conducts in human readable form
        # > e.g. "poly wish veg"
        g['conducts'] = [ c.shortname for c in Conduct.objects.filter(game__id=g['id']) ]

    return gamelist

class HomepageView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        # general statistics
        kwargs['numclans'] = Clan.objects.count()
        kwargs['numplayers'] = Player.objects.count()
        kwargs['numgames'] = Game.objects.count()
        aggr = Player.objects.aggregate(Sum('games_scummed'), Sum('wins'))
        kwargs['numscums'] = aggr['games_scummed__sum']
        kwargs['numascs'] = aggr['wins__sum']
        kwargs['numascenders'] = Player.objects.filter(wins__gt=0).count()

        # last 10 games/wins
        base_qs = Game.objects.annotate(
            playername=F('player__name'),
            dlg_fmt=F('source__dumplog_fmt')).order_by('-endtime')
        kwargs['last10games'] = bulk_upd_games(list(base_qs.values()[:10]))
        kwargs['last10wins'] = \
            bulk_upd_games(list(base_qs.filter(won=True).values()[:10]))

        return kwargs

class RulesView(TemplateView):
    template_name = 'rules.html'

class AboutView(TemplateView):
    template_name = 'about.html'

class ArchivesView(TemplateView):
    template_name = 'archives.html'

class LeaderboardsView(TemplateView):
    template_name = 'leaderboards.html'

    def get_context_data(self, **kwargs):
        # The players and clans lists produced in this function generally look
        # like this:
        # {
        #    'name': 'someplayer',
        #    OPTIONAL: (indicates this is a player in a clan)
        #    'clan': 'someclan',
        #    'stat': 304, # num of wins, etc.
        #    OPTIONAL: (indicates template should render as a link)
        #    'dumplog': 'https://hardfought.org/blah/blah.html'
        # },

        # These kwargs for annotate are exactly the same between Player and Clan.
        # *_stt is the starttime of a game, and *_dlg is the dumplog format.
        # These are necessary so that we can generate the dumplog here in the
        # view rather than telling the Game to go look up its Player and Source
        # for extra queries.
        annotate_kwargs = {
            'firstasc':        F('first_asc__endtime'),
            'firstasc_stt':    F('first_asc__starttime'),
            'firstasc_dlg':    F('fastest_realtime_asc__source__dumplog_fmt'),

            'minturns':        F('lowest_turncount_asc__turns'),
            'minturns_stt':    F('lowest_turncount_asc__starttime'),
            'minturns_dlg':    F('lowest_turncount_asc__source__dumplog_fmt'),

            'mintime':         F('fastest_realtime_asc__wallclock'),
            'mintime_stt':     F('fastest_realtime_asc__starttime'),
            'mintime_dlg':     F('fastest_realtime_asc__source__dumplog_fmt'),

            # counting with distinct=True is needed here because we aggregate
            # both conducts and achievements - the resulting SQL join produces
            # (#cond x #ach) records per Game under the hood. Counting without
            # distinct will result in that product being the result for both.
            'maxcond':         Count('max_conducts_asc__conducts', distinct=True),
            'maxcond_stt':     F('max_conducts_asc__starttime'),
            'maxcond_dlg':     F('max_conducts_asc__source__dumplog_fmt'),

            'mostachgame':     Count('max_achieves_game__achievements', distinct=True),
            'mostachgame_stt': F('max_achieves_game__starttime'),
            'mostachgame_dlg': F('max_achieves_game__source__dumplog_fmt'),

            'minscore':        F('min_score_asc__points'),
            'minscore_stt':    F('min_score_asc__starttime'),
            'minscore_dlg':    F('min_score_asc__source__dumplog_fmt'),

            'maxscore':        F('max_score_asc__points'),
            'maxscore_stt':    F('max_score_asc__starttime'),
            'maxscore_dlg':    F('max_score_asc__source__dumplog_fmt'),
        }

        # Now do the actual queries. Only 2 queries!
        allplayers = list(Player.objects
                                .filter(total_games__gt = 0)
                                .annotate(clanname=F('clan__name'), **annotate_kwargs)
                                .values())
        winplayers = [ plr for plr in allplayers if plr['wins'] > 0 ]
        allclans = list(Clan.objects
                            .filter(total_games__gt = 0)
                            .annotate(**annotate_kwargs)
                            .values())
        winclans = [ clan for clan in allclans if clan['wins'] > 0 ]
        for p in winplayers:
            if 'shadow' in p['name']:
                print('sdf', p['maxcond'])

        # This function takes one of the four lists above, and formats each
        # dictionary appropriately for consumption by the template.
        def gen_leader_list(base_list, stat, descending):
            list_out = []
            # Note: this sorting will put players with the same amount of wins
            # (or whatever metric stat is) in arbitrary order.
            # post 2021 TODO: a good enhancement would be to order it by the
            # first player to get there
            for elem in sorted(base_list, key=lambda E: E[stat], reverse=descending):
                if not stat in elem or elem[stat] is None:
                    # could indicate a field was not correctly populated during
                    # aggregation, such as a Player who has wins > 0 but
                    # first_asc is None
                    logger.error('malformed query result for leaderboards')
                    logger.error('stat = %s element = %s', stat, str(elem))
                    return []
                # elem is either a player or a clan, but this loop doesn't care
                # which
                converted = {
                    'name': elem['name'],
                    'stat': elem[stat],
                }
                if 'clanname' in elem and elem['clanname'] is not None:
                    # this is a player, and we want to show the clan
                    converted['clan'] = elem['clanname']
                if (stat + '_stt') in elem:
                    # this is a stat representing a single game, so it has an
                    # associated dumplog
                    converted['dumplog'] = \
                        dumplog_utils.format_dumplog(elem[stat + '_dlg'],
                                                     elem['name'],
                                                     elem[stat + '_stt'])
                list_out.append(converted)
            return list_out

        # The order of these leaderboards determines the order on the page and
        # in the combo box.
        leaderboards = [
            # if stat is absent, then just use id as the stat
            { 'id': 'mostasc', 'stat': 'wins', 'descending': True, 'wins_only': True,
              'title': 'Most Ascensions', 'columntitle': 'wins' },
            { 'id': 'firstasc', 'descending': False, 'wins_only': True,
              'title': 'Earliest Ascension', 'columntitle': 'time' },
            { 'id': 'minturns', 'descending': False, 'wins_only': True,
              'title': 'Lowest Turncount', 'columntitle': 'turns' },
            { 'id': 'mintime', 'descending': False, 'wins_only': True,
              'title': 'Fastest Realtime', 'columntitle': 'wallclock' },
            { 'id': 'maxcond', 'descending': True, 'wins_only': True,
              'title': 'Most Conducts in One Ascension', 'columntitle': 'conducts' },
            { 'id': 'mostachgame', 'descending': True, 'wins_only': True,
              'title': 'Most Achievements in One Game', 'columntitle': 'achievements' },
            { 'id': 'mostach', 'descending': True, 'stat': 'unique_achievements',
              'wins_only': False,
              'title': 'Most Achievements Overall', 'columntitle': 'achievements' },
            { 'id': 'minscore', 'descending': False, 'wins_only': True,
              'title': 'Lowest Scoring Ascension', 'columntitle': 'points' },
            { 'id': 'maxscore', 'descending': True, 'wins_only': True,
              'title': 'Highest Scoring Ascension', 'columntitle': 'points' },
            { 'id': 'longstreak', 'stat': 'longest_streak', 'descending': True,
              'wins_only': True,
              'title': 'Longest Streak', 'columntitle': 'streak length' },
            { 'id': 'uniquedeaths', 'stat': 'unique_deaths', 'descending': True,
              'wins_only': False,
              'title': 'Most Unique Deaths', 'columntitle': 'deaths' },
            { 'id': 'uniqueasc', 'stat': 'unique_ascs', 'descending': True,
              'wins_only': True,
              'title': 'Most Unique Ascension Combos', 'columntitle': 'combos' },
            { 'id': 'mostgames', 'stat': 'games_over_1000_turns', 'descending': True,
              'wins_only': False,
              'title': 'Most Games over 1000 Turns', 'columntitle': 'games' },
        ]
        # now add player/clan data to the leaderboards
        for L in leaderboards:
            L['players'] = gen_leader_list(winplayers if L['wins_only'] else allplayers,
                                           L['stat'] if 'stat' in L else L['id'],
                                           L['descending'])
            L['clans'] = gen_leader_list(winclans if L['wins_only'] else allclans,
                                         L['stat'] if 'stat' in L else L['id'],
                                         L['descending'])
        kwargs['leaderboards'] = leaderboards
        return kwargs

class PlayersView(TemplateView):
    template_name = 'players.html'

    def get_context_data(self, **kwargs):
        kwargs['players'] = Player.objects.order_by('-wins', 'name')
        return kwargs

class ClansView(TemplateView):
    template_name = 'clans.html'

    def get_context_data(self, **kwargs):
        # Query for player-clan relationships.
        plr2clan = list(Player.objects.filter(clan__isnull=False)
                        .annotate(clan_name=F('clan__name'))
                        .order_by('name')
                        .values('name','clan_name','clan_admin'))

        # convert:
        # [{'name': 'bob', 'clan_name': 'foo', 'clan_admin': True}, ...]
        #   => { 'foo': [{ 'name': 'bob', 'admin': True}, ...] }
        clan_members = {}
        for plr in plr2clan:
            pname, cname = plr['name'], plr['clan_name']
            if not cname in clan_members:
                # new clan, add it as new list
                clan_members[cname] = []
            clan_members[cname].append({
                'name': pname,
                'admin': plr['clan_admin']
            })

        # All clans list, convert to list to only query db once.
        clanlist = list(Clan.objects.order_by('-wins', 'name').values())

        # Now insert the lists of members.
        for clan in clanlist:
            if not clan['name'] in clan_members:
                logging.error('Clan %s exists in db but has no members!', clan['name'])
                continue
            clan['members'] = clan_members[clan['name']]

        # Pass on to template.
        kwargs['clans'] = clanlist
        return kwargs

class SinglePlayerOrClanView(TemplateView):
    template_name = 'singleplayerorclan.html'

    def get_context_data(self, **kwargs):
        if 'clanname' in kwargs:
            kwargs['isClan'] = True
            kwargs['header_key'] = 'clans'
            clan = get_object_or_404(Clan, name=kwargs['clanname'])
            kwargs['player_or_clan'] = clan
            members = Player.objects.filter(clan=clan).order_by('-clan_admin', 'name') \
                            .values('id', 'name','clan_admin')
            kwargs['members'] = members

            # flatten members' names into a list for Game filterings
            member_ids = [ m['id'] for m in members ]

            # for a clan, we want to filter games from any of its members
            base_game_qs = Game.objects.filter(player__in=member_ids)

        elif 'playername' in kwargs:
            kwargs['isClan'] = False
            kwargs['header_key'] = 'players'
            player = get_object_or_404(Player, name=kwargs['playername'])
            kwargs['player_or_clan'] = player
            base_game_qs = Game.objects.filter(player=player.id)

        else:
            logger.error('single player/clan view without clan or player name')
            raise ValueError

        # add information to the Game queryset that lets us generate dumplogs,
        # and default sorting
        base_game_qs = base_game_qs.annotate(playername=F('player__name'),
                                             dlg_fmt=F('source__dumplog_fmt')) \
                                   .order_by('-endtime')
        kwargs['ascensions'] = \
            bulk_upd_games(list(base_game_qs.filter(won=True).values()))
        # 10 most recent games
        kwargs['recentgames'] = \
            bulk_upd_games(list(base_game_qs[:10].values()))

        # post 2021 TODO: this currently only gets the deaths, no other details
        kwargs['uniquedeaths'] = sorted(list(uniqdeaths.compile_unique_deaths(base_game_qs)))

        # a little subquerying for achievements...
        gameswith_ach = base_game_qs.filter(achievements__pk=OuterRef('pk'))
        achievements = Achievement.objects.annotate(obtained=Exists(gameswith_ach))
        kwargs['achievements'] = achievements

        return kwargs

class TrophiesView(TemplateView):
    template_name = 'trophies.html'

    def get_context_data(self, **kwargs):
        # only do 3 queries!
        trophies_def = list(Trophy.objects.values('name','description'))
        clan2troph = list(Clan.objects
                              .annotate(field=Value('clans'),
                                        numtroph=Count('trophies__id'))
                              .filter(numtroph__gt=0)
                              .values('name','trophies__name','field'))
        plr2troph = list(Player.objects
                               .annotate(field=Value('players'),
                                         numtroph=Count('trophies__id'))
                               .filter(numtroph__gt=0)
                               .values('name','trophies__name','field'))
        alltroph = clan2troph + plr2troph

        # we need to show all trophies regardless of anyone having them, so
        # first populate the basic structure we need to send to the template
        trophies = {}
        for t in trophies_def:
            trophies[t['name']] = {
                'description' : t['description'],
                'players': [],
                'clans': []
            }

        # lists are [{'name': <player/clan name>, 'trophies__name': 'Both Genders', 'trophies__description': '<desc>', 'field': 'players'}, ...]
        # convert to { 'Both Genders': { 'players': [...], 'clans': [...], 'description': '...' }, ...}
        for a in alltroph:
            plr_or_clan_name = a['name']
            tname            = a['trophies__name']
            field            = a['field'] # either "players" or "clans"
            trophies[tname][field].append(plr_or_clan_name)

        kwargs['trophies'] = trophies
        return kwargs

class ClanMgmtView(View):
    template_name = 'clanmgmt.html'
    # TODO: Clan interactions should maybe force a re-aggregation?
    # Or if not, clan management page should say that data will be stale for up to X minutes

    def get_player(self, request_user):
        # Attempt to get the player linked with this user ID. Contains some
        # checks against weird edge cases.
        # Argument is request.user from an HTTP request.
        # If we seriously can't find a player, raise Player.DoesNotExist; the
        # expectation is that the caller will return an appropriate error (500)
        # to the browser.
        try:
            return Player.objects.get(user=request_user.id)
        except Player.DoesNotExist:
            logger.warning('No Player found linked to logged-in user (id %s, name %s)',
                           request_user.id, request_user)
            try:
                # ok THIS shouldn't fail... we really shouldn't have allowed a
                # user to exist without a Player of corresponding name
                player = Player.objects.get(name=request_user)
                player.user = request_user
                player.save()
                logger.warning('Fell back on linking to existing Player named %s',
                               request_user)
                return player
            except Player.DoesNotExist as e:
                logger.error('No Player found with name of logged in user (name %s)',
                             request_user)
                raise e

    def get_context_data(self, **kwargs):
        user = self.request.user
        # we assume the player is already known to exist since both get() and
        # post() check for it
        # TODO (lowish priority): player should be passed in as kwargs already.
        player = self.get_player(user)

        kwargs['me'] = player
        kwargs['clan'] = None
        clan = player.clan
        if clan is not None:
            kwargs['clan'] = clan
            kwargs['members'] = Player.objects.filter(clan=clan).order_by('-clan_admin','name')
            kwargs['invitees'] = clan.invitees.all().order_by('name')
        kwargs['invites'] = player.invites.all().order_by('name')

        kwargs['clan_freeze'] = self.clan_freeze_in_effect()

        if 'invite_member_form' not in kwargs:
            kwargs['invite_member_form'] = InviteMemberForm()
        if 'create_clan_form' not in kwargs:
            kwargs['create_clan_form'] = CreateClanForm()

        return kwargs

    def clan_freeze_in_effect(self):
        return settings.CLAN_FREEZE_TIME <= datetime.now(tz=timezone.utc)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login')

        # TODO: This case is duplicated from the POST below. Ideally they should
        # be unified.
        try:
            self.get_player(request.user)
        except Player.DoesNotExist:
            return HttpResponse(status=500)

        return render(request, self.template_name, self.get_context_data(**kwargs))

    # FUTURE TODO:
    # This isn't a very Djangoish way of doing things to have a bunch of
    # different post requests to clanmgmt. Ideally they'd all be different
    # endpoints, but not take you to other pages.
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login')

        # if we passed the auth test above then this shouldn't fail...
        # but it could if the Player db is wiped without the auth.user db being wiped.
        try:
            player = self.get_player(request.user)
        except Player.DoesNotExist:
            return HttpResponse(status=500)
        ctx = {}

        # People could theoretically mess with POST requests and trigger
        # unexpected behavior. This logic should guard against things like that
        # while logging that it happened so we can see if it's a bug or someone
        # trying to exploit something.
        #
        # How things are logged:
        # error - we actually don't know what to do and the site will have to
        # inform the user a serious error occurred.
        # warning - something happened that the UI is not supposed to allow, but
        # we can handle it gracefully.
        # info - normal events.

        if 'create_clan' in request.POST:
            self.create_clan(request, player, ctx)

        elif 'invite' in request.POST:
            self.invite_to_clan(request, player, ctx)

        elif 'leave' in request.POST:
            self.leave_clan(request, player, ctx)

        elif 'disband' in request.POST:
            self.disband_clan(request, player, ctx)

        elif 'join_clan' in request.POST:
            self.join_clan(request, player, ctx)

        elif 'rescind' in request.POST:
            self.rescind_invite(request, player, ctx)

        elif 'adminify' in request.POST:
            self.make_admin(request, player, ctx)

        elif 'kick' in request.POST:
            self.kick_member(request, player, ctx)

        return render(request, self.template_name, self.get_context_data(**ctx))

    # Helper function triggered when a create_clan POST request comes in
    def create_clan(self, request, player, ctx):
        create_clan_form = CreateClanForm(request.POST)

        if not create_clan_form.is_valid():
            ctx['create_clan_form'] = create_clan_form
            return

        new_clan_name = create_clan_form.cleaned_data['clan_name']

        # clan freeze must not be in effect
        if self.clan_freeze_in_effect():
            logger.warning('%s attempted to make a clan during freeze',
                           player.name)
            ctx['errmsg'] = 'Clans cannot be created with clan freeze in effect'
            return

        # new clan name must be unique
        if Clan.objects.filter(name=new_clan_name).exists():
            ctx['errmsg'] = 'That clan already exists'
            return

        # player must not already be in a clan
        if player.clan is not None:
            logger.warning('%s attempted to make a clan while already in one',
                           player.name)
            ctx['errmsg'] = 'You are already in a clan'
            return

        # if we got here, we're good to create the clan, with the creator as its
        # admin
        newclan = Clan(name=new_clan_name)
        newclan.save()
        player.clan = newclan
        player.clan_admin = True
        player.save()
        logger.info('%s created clan %s', player.name, newclan.name)

    # Helper function triggered when a invite-to-clan POST request comes in
    def invite_to_clan(self, request, player, ctx):
        invite_form = InviteMemberForm(request.POST)

        if not invite_form.is_valid():
            ctx['invite_member_form'] = invite_form
            return

        # invites are pointless when clan freeze is in effect
        if self.clan_freeze_in_effect():
            ctx['errmsg'] = 'Invites cannot be made with clan freeze in effect'
            return

        # must have a clan to invite to
        if player.clan is None:
            logger.warning('%s attempted to invite without being in a clan',
                           player.name)
            ctx['errmsg'] = "You can't invite people without being in a clan"
            return

        # only clan admins can invite players
        if not player.clan_admin:
            logger.warning('%s attempted to invite without being admin',
                           player.name)
            ctx['errmsg'] = "You can't invite people because you aren't a clan admin"
            return

        # if we got here, we're good to attempt the invite
        invitee_name = invite_form.cleaned_data['invitee']
        try:
            # retrieve player if exists in our database, if not
            # but they are in dgl database, create the player in our
            # database (we need to do this because we need to record
            # them as having an invite)
            invitee = hardfought_utils.find_player(invitee_name)
            invitee.invites.add(player.clan)
            logger.info('%s invited %s to clan %s',
                        player.name, invitee_name, player.clan.name)
        except Player.DoesNotExist:
            logger.warning('%s attempted to invite nonexistent player %s',
                           player.name, invitee_name)
            ctx['errmsg'] = 'No such player exists'

    # Helper function triggered when "leave" is clicked
    def leave_clan(self, request, player, ctx):
        clan = player.clan

        # must actually have a clan
        if clan is None:
            logger.warning('%s attempted to leave without being in a clan',
                           player.name)
            ctx['errmsg'] = "You're not in a clan to leave"
            return

        # ideally "leave clan" shouldn't be displayed if the player is the only
        # member of their clan, but if the POST is submitted anyway, disband the
        # clan
        if not Player.objects.filter(clan=clan).exclude(id=player.id).exists():
            self.disband_clan(request, player, ctx)
            return

        # don't allow if this would leave the clan admin-less
        if not Player.objects.filter(clan=player.clan, clan_admin=True).exclude(id=player.id).exists():
            logger.warning('%s attempted to leave and cause admin-less clan',
                           player.name)
            ctx['errmsg'] = 'You cannot leave this clan because it would leave it without an admin'
            return

        # if we got here, we're good to leave the clan
        save_clan_name = player.clan.name
        player.clan = None
        player.save()
        logger.info('%s left clan %s', player.name, save_clan_name)

    # Helper function triggered when "disband" is clicked
    def disband_clan(self, request, player, ctx):
        clan = player.clan

        # doesn't make sense if player isn't in a clan
        if clan is None:
            logger.warning('%s attempted to disband with no clan', player.name)
            ctx['errmsg'] = 'You are not in a clan to disband'
            return

        # only admins can disband the clan
        if not player.clan_admin:
            logger.warning('%s attempted to disband as non-admin', player.name)
            ctx['errmsg'] = 'Only clan admins can disband your clan'
            return

        # if we got here, we're good to leave the clan
        clan_members = Player.objects.filter(clan=player.clan)
        for member in clan_members:
            # setting .clan to None is not technically needed because the
            # model has SET_NULL for when the clan is deleted, but why not be
            # explicit?
            member.clan = None
            member.clan_admin = False
            member.save()
        save_clan_name = player.clan.name
        clan.delete()
        logger.info('%s disbanded clan %s',
                    player.name, save_clan_name)

    # Helper function triggered when a clan's invite is clicked
    def join_clan(self, request, player, ctx):
        join_clan_id = request.POST['join_clan_id']

        # joins are not allowed when clan freeze is in effect
        if self.clan_freeze_in_effect():
            logger.warning('%s attempted to join a clan during freeze',
                           player.name)
            ctx['errmsg'] = 'You cannot join a clan with clan freeze in effect'
            return

        # can't join a clan if already in one
        if player.clan:
            logger.warning('%s attempted to join clan %s while already in a clan',
                           player.name, join_clan_id)
            ctx['errmsg'] = "You can't join that clan because you're already in one"
            return

        # clan id actually needs to exist
        # this could theoretically happen normally, where one player loads the
        # clan management page and has an invite for another clan, which has
        # disbanded by the time they submit the join request.
        try:
            newclan = Clan.objects.get(id=join_clan_id)
        except Clan.DoesNotExist:
            logger.warning('%s attempted to join nonexistent clan id %s',
                           player.name, join_clan_id)
            ctx['errmsg'] = "You tried to join a clan that doesn't exist"
            return

        # clan needs to have actually extended the invite
        # (this shouldn't come up in normal use)
        if not player.invites.filter(id=join_clan_id):
            logger.warning('%s attempted to join clan %s without an invitation',
                           player.name, newclan.name)
            ctx['errmsg'] = "That clan has not invited you"
            return

        # clan can't be full
        if Player.objects.filter(clan=newclan).count() >= settings.MAX_CLAN_PLAYERS:
            logger.info('%s attempted to join full clan %s',
                        player.name, newclan.name)
            ctx['errmsg'] = "That clan is full"
            return

        # if we got here, we're good to join the clan
        player.clan = newclan
        if player.clan_admin:
            logger.warning('%s, while joining, was somehow already an admin',
                           player.name)
        player.clan_admin = False # to be safe
        player.save()
        # A bit questionable whether the invite should be left in place or
        # removed here, but we decided that if a player leaves or is kicked from
        # the clan, it's cleaner if they have to ask for the invite again
        player.invites.remove(newclan)
        logger.info('%s accepted invite to clan %s',
                    player.name, newclan.name)

    # Helper function for common logic between rescinding, making admin, and
    # kicking - all of these take a player ID and require similar checks to be made.
    # It does NOT check that the other player is in the clan, since invites
    # don't require that.
    # This returns the Player associated with oth_id.
    def clan_admin_other_member_checks(self, request, player, ctx, oth_id, action):
        # other player must exist
        try:
            otherplayer = Player.objects.get(id=oth_id)
        except Player.DoesNotExist:
            logger.warning('%s attempted to %s with nonexistent id %s',
                           player.name, action, oth_id)
            ctx['errmsg'] = 'The player was not found'
            return None

        # player must be in a clan
        if player.clan is None:
            logger.warning('%s attempted to %s without being in a clan',
                           player.name, action)
            ctx['errmsg'] = "You can't %s if you're not in a clan" % (action)
            return None

        # player must be an admin of their clan
        if not player.clan_admin:
            logger.warning('%s attempted to %s without being an admin',
                           player.name, action)
            ctx['errmsg'] = 'Only admins can %s' % (action)
            return None

        return otherplayer

    # Helper function triggered when "Rescind" is clicked on an invited player
    def rescind_invite(self, request, player, ctx):
        # TODO? all of these helpers should test that the key is in POST, and if
        # not, log an error and return
        rescindee_id = request.POST['rescind_id']
        rescindee = self.clan_admin_other_member_checks(request, player, ctx,
                                                        rescindee_id, "rescind")
        if rescindee is None:
            return

        # if we passed checks, we're good to rescind the invite
        rescindee.invites.remove(player.clan)
        logger.info("%s rescinded clan %s's invite to %s",
                    player.name, player.clan.name, rescindee.name)

    # Helper function triggered when "Make Admin" is clicked on a clan member
    def make_admin(self, request, player, ctx):
        new_admin_id = request.POST['kick_or_admin_id']
        new_admin = self.clan_admin_other_member_checks(request, player, ctx,
                                                        new_admin_id, "make admin")
        if new_admin is None:
            return

        # other player must be in this clan
        if player.clan != new_admin.clan:
            logger.warning('%s attempted to make %s (not in their clan) an admin',
                           player.name, new_admin.name)
            ctx['errmsg'] = '%s is not in your clan' % (new_admin.name)
            return

        # can't make someone an admin who's already an admin
        if new_admin.clan_admin:
            logger.warning('%s attempted to make %s an admin, but they already were',
                           player.name, new_admin.name)
            ctx['errmsg'] = '%s is already a clan admin' % (new_admin.name)
            return

        # if we passed checks, we're good to make this person an admin
        new_admin.clan_admin = True
        new_admin.save()
        logger.info('%s made %s an admin of clan %s',
                    player.name, new_admin.name, player.clan.name)

    # Helper function triggered when "Kick" is clicked on a clan member
    def kick_member(self, request, player, ctx):
        kickee_id = request.POST['kick_or_admin_id']
        kickee = self.clan_admin_other_member_checks(request, player, ctx,
                                                     kickee_id, "kick")
        if kickee is None:
            return

        # other player must be in this clan
        if player.clan != kickee.clan:
            logger.warning('%s attempted to kick %s (not in their clan)',
                           player.name, kickee.name)
            ctx['errmsg'] = '%s is not in your clan' % (kickee.name)
            return

        if kickee_id == player.id:
            # the UI should not allow this, but "kick self out" is basically the
            # same as leaving...
            logger.warning('%s is kicking themself out of their clan, not leaving',
                           player.name)
            self.leave_clan(request, player, ctx)
            return

        # if we passed checks, we're good to kick this player out of the clan
        kickee.clan = None
        kickee.clan_admin = False
        kickee.save()
        logger.info('%s kicked %s out of clan %s',
                    player.name, kickee.name, player.clan.name)
        # FUTURE TODO: would be nice if this and all the other post operations
        # also updated a context message that gets displayed to show success; in
        # this case it would be "Successfully kicked foo out of the clan"

    # FUTURE TODO: functionality for a clanless player to request becoming a
    # member of a clan they input, admins can accept (inverse of invites)
    # FUTURE TODO: functionality for a clanless player to raise a flag saying
    # "looking for a clan!" and all such players are listed either publicly or
    # to clan admins (probably publicly)
