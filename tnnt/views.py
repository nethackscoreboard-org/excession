from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.db.models import Exists, OuterRef, F, Count
from scoreboard.models import Player, Clan, Game, Achievement
from tnnt.forms import CreateClanForm, InviteMemberForm
from django.http import HttpResponse, HttpResponseRedirect
from . import hardfought_utils # find_player
from . import settings
from datetime import datetime, timezone
import logging
from django.db import connection # TODO: for debugging only

logger = logging.getLogger() # use root logger

class HomepageView(TemplateView):
    template_name = 'index.html'

class RulesView(TemplateView):
    template_name = 'rules.html'

class AboutView(TemplateView):
    template_name = 'about.html'

class ArchivesView(TemplateView):
    template_name = 'archives.html'

class LeaderboardsView(TemplateView):
    template_name = 'leaderboards.html'

    def get_context_data(self, **kwargs):
        # Due to TNNT 2021 deadlines, this may need to be optimized more, or
        # possibly it will never put too much strain on the database and it's
        # fine. Time will tell.

        # These kwargs for annotate are exactly the same between Player and Clan
        annotate_kwargs = {
        #     'firstasc': F('first_asc__endtime'),
        #     'minturns': F('lowest_turncount_asc__turns'),
        #     'mintime': F('fastest_realtime_asc__wallclock'),
        #     'maxcond': Count('max_conducts_asc__conducts'),
        #     'mostachgame': Count('max_achieves_game__achievements'),
        #     'minscore': F('min_score_asc__points'),
        #     'maxscore': F('max_score_asc__points'),
        }
        # Similarly these are the exact same. (All LeaderboardBaseFields that
        # are foreign keys to Game go here.) This saves a number of database
        # accesses to get the Game objects and their data when we use them
        # in the template, but it will NOT prevent each Game from making a
        # further two queries to Source and back to Player when get_dumplog is
        # called on them.
        select_related_args = [
            'first_asc',
            'lowest_turncount_asc',
            'fastest_realtime_asc',
            'max_conducts_asc',
            'max_achieves_game',
            'min_score_asc',
            'max_score_asc'
        ]
        # TODO: We may want to come back to [the approach of putting the data in
        # lists]... problem with putting it in lists is that you lose the
        # ability to go into related models like Game
        norm_playerdata = Player.objects.filter(total_games__gt=0) \
            .select_related(*select_related_args) \
            .annotate(**annotate_kwargs).all()
        norm_clandata = Clan.objects.filter(total_games__gt=0) \
            .select_related(*select_related_args) \
            .annotate(**annotate_kwargs).all()
        asc_playerdata = [ P for P in norm_playerdata if P.wins > 0 ]
        asc_clandata = [ C for C in norm_clandata if C.wins > 0 ]

        kwargs['allboards'] = {
            'mostasc': {
                # Note: all this sorting will put players with the same amount
                # of wins (or whatever metric) in arbitrary order.
                'players': sorted(asc_playerdata, key=lambda P: P.wins, reverse=True),
                'clans': sorted(asc_clandata, key=lambda C: C.wins, reverse=True)
            },
            'firstasc': {
                'players': sorted(asc_playerdata, key=lambda P: P.first_asc.endtime),
                'clans': sorted(asc_clandata, key=lambda C: C.first_asc.endtime)
            },
            'minturns': {
                'players': sorted(asc_playerdata, key=lambda P: P.lowest_turncount_asc.turns),
                'clans': sorted(asc_clandata, key=lambda C: C.lowest_turncount_asc.turns)
            },
            'mintime': {
                'players': sorted(asc_playerdata, key=lambda P: P.fastest_realtime_asc.wallclock),
                'clans': sorted(asc_clandata, key=lambda C: C.fastest_realtime_asc.wallclock)
            },
            'maxcond': {
                # These two are ripe for some optimization as well. For one, by
                # using a predefined function and not a lambda it could bulk
                # count the conducts. But this may still be possible to do as
                # part of the large query.
                'players': sorted(asc_playerdata,
                                  key=lambda P: P.max_conducts_asc.conducts.count(),
                                  reverse=True),
                'clans': sorted(asc_clandata,
                                key=lambda C: C.max_conducts_asc.conducts.count(),
                                reverse=True)
            },
            'mostachgame': {
                'players': sorted(norm_playerdata,
                                  key=lambda P: 0 if P.max_achieves_game is None
                                                else P.max_achieves_game.achievements.count(),
                                  reverse=True),
                'clans': sorted(norm_clandata,
                                key=lambda C: 0 if C.max_achieves_game is None
                                              else C.max_achieves_game.achievements.count(),
                                reverse=True)
            },
            'mostach': {
                'players': sorted(norm_playerdata, key=lambda P: P.unique_achievements, reverse=True),
                'clans': sorted(norm_clandata, key=lambda C: C.unique_achievements, reverse=True)
            },
            'minscore': {
                'players': sorted(asc_playerdata, key=lambda P: P.min_score_asc.points),
                'clans': sorted(asc_clandata, key=lambda C: C.min_score_asc.points)
            },
            'maxscore': {
                'players': sorted(asc_playerdata, key=lambda P: P.max_score_asc.points, reverse=True),
                'clans': sorted(asc_clandata, key=lambda C: C.max_score_asc, reverse=True)
            },
            'longstreak': {
                'players': sorted(asc_playerdata, key=lambda P: P.longest_streak, reverse=True),
                'clans': sorted(asc_clandata, key=lambda C: C.longest_streak, reverse=True)
            },
            'uniquedeaths': {
                'players': sorted(norm_playerdata, key=lambda P: P.unique_deaths, reverse=True),
                'clans': sorted(norm_clandata, key=lambda C: C.unique_deaths, reverse=True)
            },
            'uniqueasc': {
                'players': sorted(asc_playerdata, key=lambda P: P.unique_ascs, reverse=True),
                'clans': sorted(asc_clandata, key=lambda C: C.unique_ascs, reverse=True)
            },
            'mostgames': {
                'players': sorted(norm_playerdata, key=lambda P: P.games_over_1000_turns, reverse=True),
                'clans': sorted(norm_clandata, key=lambda C: C.games_over_1000_turns, reverse=True)
            },
        }
        return kwargs

    # TODO: for debugging and db stats tracking only. Delete this later.
    def get(self, request, *args, **kwargs):
        strt_q = len(connection.queries)
        rendered = render(request, self.template_name, self.get_context_data(**kwargs))
        end_q = len(connection.queries)
        logger.debug('metrics: leaderboards executed %s queries', end_q - strt_q)
        return rendered

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

class SinglePlayerView(TemplateView):
    template_name = 'singleplayer.html'

    def get_context_data(self, **kwargs):
        kwargs['player'] = get_object_or_404(Player, name=kwargs['playername'])

        gameswith_ach = Game.objects \
            .filter(player=kwargs['player'],
                    achievements__pk=OuterRef('pk'))
        achievements = Achievement.objects.annotate(obtained=Exists(gameswith_ach))
        kwargs['achievements'] = achievements

        kwargs['ascensions'] = \
            Game.objects.filter(player=kwargs['player'], won=True).order_by('-endtime')
        # 10 most recent games
        kwargs['recentgames'] = \
            Game.objects.filter(player=kwargs['player']).order_by('-endtime')[:10]
        return kwargs

class ClanMgmtView(View):
    template_name = 'clanmgmt.html'

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
