from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render
from scoreboard.models import Player, Clan
from tnnt.forms import CreateClanForm, InviteMemberForm
from django.http import HttpResponseRedirect
from . import hardfought_utils # find_player
from . import settings
from datetime import datetime
import logging

logger = logging.getLogger() # use root logger

class HomepageView(TemplateView):
    template_name = 'index.html'

class RulesView(TemplateView):
    template_name = 'rules.html'

class AboutView(TemplateView):
    template_name = 'about.html'

class ArchivesView(TemplateView):
    template_name = 'archives.html'

class ClanMgmtView(View):
    template_name = 'clanmgmt.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        # look up their clan
        kwargs['clan'] = None
        try:
            player = Player.objects.get(user=user.id)
            kwargs['me'] = player
            clan = player.clan
            if clan is not None:
                kwargs['clan'] = clan
                kwargs['members'] = Player.objects.filter(clan=clan).order_by('-clan_admin','name')
                kwargs['invitees'] = clan.invitees.all().order_by('name')
            kwargs['invites'] = player.invites.all().order_by('name')
        except Player.DoesNotExist:
            clan = None

        kwargs['clan_freeze'] = self.clan_freeze_in_effect()

        if 'invite_member_form' not in kwargs:
            kwargs['invite_member_form'] = InviteMemberForm()
        if 'create_clan_form' not in kwargs:
            kwargs['create_clan_form'] = CreateClanForm()

        return kwargs

    def clan_freeze_in_effect(self):
        return datetime.fromisoformat(settings.CLAN_FREEZE_TIME) <= datetime.now()

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login')
        return render(request, self.template_name, self.get_context_data(**kwargs))

    # FUTURE TODO:
    # This isn't a very Djangoish way of doing things to have a bunch of
    # different post requests to clanmgmt. Ideally they'd all be different
    # endpoints, but not take you to other pages.
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login')

        # if we passed the auth test above then this shouldn't fail...
        player = Player.objects.get(user=request.user.id)
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
