import asyncio
import json
import logging
import traceback
from io import BytesIO
from pathlib import Path

import discord
from discord import app_commands
from engine import Game
from cards import render_card, render_lobby, render_winner
WORLD_ROLES = {'South America', 'Europe', 'Africa', 'Oceania', 'Asia'}
REGION_ROLES = WORLD_ROLES | {'North America'}


def region_team(roles):
    north = 'North America' in roles
    world = bool(WORLD_ROLES & roles)
    if north == world:
        return None
    return 'north' if north else 'world'


def opposing_players(winner, players, roles):
    side = region_team(roles.get(winner, set()))
    if side is None:
        return []
    other = 'world' if side == 'north' else 'north'
    return list(dict.fromkeys(p for p in players if region_team(roles.get(p, set())) == other))

ROOT = Path(__file__).resolve().parent
MODE_IMAGES = {
    'classic': 'arena-classic.png',
    'sexes': 'arena-sexes.png',
    'winner': 'arena-winner.png',
    'world': 'arena-northamericavworld.png',
}


def lobby_image_path(mode):
    selected = ROOT / MODE_IMAGES.get(mode, 'arena-start.png')
    return selected if selected.is_file() else ROOT / 'arena-start.png'

CONFIG = json.loads((ROOT / 'config.json').read_text(encoding='utf-8-sig'))
SERVER_ID = int(CONFIG['server_id'])
EVENT_DELAY = max(5, min(120, int(CONFIG.get('event_seconds', 5))))
ROUND_DELAY = max(10, min(300, int(CONFIG.get('between_round_seconds', 5))))
sessions = {}


def report_error(label, error):
    original = getattr(error, 'original', error)
    detail = ''.join(traceback.format_exception(type(original), original, original.__traceback__))
    token = CONFIG.get('token', '')
    if token:
        detail = detail.replace(token, '[TOKEN REDACTED]')
    logging.error('%s\n%s', label, detail)
    return original


def lobby_role_ping(guild):
    role = discord.utils.get(guild.roles, name='NSFW Hangrygames')
    if role is None:
        return {}
    return {'content': role.mention,
            'allowed_mentions': discord.AllowedMentions(everyone=False, users=False, roles=[role], replied_user=False)}


def manager(user):
    return user.guild_permissions.manage_guild or any(role.name == 'Vice Admin' for role in user.roles)


class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default(), allowed_mentions=discord.AllowedMentions.none())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        server = discord.Object(id=SERVER_ID)
        self.tree.copy_global_to(guild=server)
        await self.tree.sync(guild=server)

    async def on_ready(self):
        print(f'Ready as {self.user}. Use /game create in your server.')


client = Client()
group = app_commands.Group(name='game', description='VICE • After Dark Arena game', guild_only=True)
client.tree.add_command(group)


class Lobby(discord.ui.View):
    def __init__(self, interaction, mode='classic', participant_goal=None):
        super().__init__(timeout=24 * 60 * 60)
        self.host = interaction.user.id
        self.channel = interaction.channel
        self.key = interaction.channel_id
        self.players = []
        self.mode = mode
        self.participant_goal = participant_goal
        self.teams = {}
        self.region_roles = {}
        self.profiles = {}
        self.avatar_assets = {}
        self.state = 'Lobby open'
        self.message = None
        self.messages = []
        self.task = None
        self.lock = asyncio.Lock()

    def embed(self):
        roster = '\n'.join(f'{i}. <@{p}>' for i, p in enumerate(self.players, 1)) or 'Do NOT disappoint Miss Reyes. JOIN UP, HOE!'
        result = discord.Embed(title='✦ VICE • AFTER DARK ARENA ✦', color=0xBE428B,
            description='Time to make some very poor decisions. Are you ready to risk it all? \n'
                        'Join to participate — come get rowdy with us!\n\n' + roster)
        result.add_field(name='Host', value=f'<@{self.host}>')
        result.add_field(name='Players', value=f'{len(self.players)}/80')
        result.add_field(name='Auto-start', value=f'{len(self.players)}/{self.participant_goal} players — starts when the goal is reached' if self.participant_goal else 'Off — manual start', inline=False)
        mode_text = {
            'world': 'North America vs. the World — who will TRUMP the other? Umm... yeah, Kylie apologizes for that horrible pun. Please do not murder her.',
            'classic': 'Classic — first death and unexpected deaths finna flash for mommy Reyes! If you win, you have the distinct honor of choosing 3 people to flash!',
            'sexes': 'Battle of the Sexes — if the winner is a male, all women to flash • if the winner is female, all men to flash!',
            'winner': 'Winner Flashes — if you win, it is your time to sin!',
        }[self.mode]
        result.add_field(name='Mode', value=mode_text, inline=False)
        if self.mode != 'classic':
            result.add_field(name='Joining means', value='WOOO HOOOOO! Time to add some extra spice into this game!', inline=False)
        result.set_image(url=f'attachment://{MODE_IMAGES[self.mode]}')
        result.set_footer(text=f'{self.state} • lobby expires after 24 hours of inactivity')
        return result

    def authorized(self, user):
        return user.id == self.host or manager(user)

    def release(self):
        if sessions.get(self.key) is self:
            sessions.pop(self.key)
        self.stop()

    async def refresh_messages(self, active=True):
        remaining = []
        for message in self.messages:
            try:
                await message.edit(embed=self.embed(), view=self if active else None)
                remaining.append(message)
            except discord.NotFound:
                continue
            except discord.HTTPException as error:
                report_error('Scream for Kylie - I could not refresh a copy of the lobby!', error)
                remaining.append(message)
        self.messages = remaining

    async def interaction_check(self, interaction):
        if self.state != 'Lobby open':
            await interaction.response.send_message('This lobby is closed, sorry boo.', ephemeral=True)
            return False
        return True

    async def change_player(self, interaction, joining):
        await interaction.response.defer(ephemeral=True)
        async with self.lock:
            if self.state != 'Lobby open':
                return await interaction.followup.send('This lobby is closed, sorry boo.', ephemeral=True)
            uid = interaction.user.id
            if joining:
                if uid in self.players:
                    return await interaction.followup.send('You goose, you have already joined!', ephemeral=True)
                if len(self.players) >= 80:
                    return await interaction.followup.send('This lobby is more full than a turducken. Please wait until the next round!', ephemeral=True)
                self.players.append(uid)
                roles = {r.name for r in interaction.user.roles}
                self.teams[uid] = roles & {'He/Him', 'She/Her'}
                self.region_roles[uid] = roles & REGION_ROLES
                self.profiles[uid] = interaction.user.display_name
                self.avatar_assets[uid] = interaction.user.display_avatar.with_static_format('png').with_size(256)
            elif uid in self.players:
                self.players.remove(uid)
                self.teams.pop(uid, None)
                self.region_roles.pop(uid, None)
                self.profiles.pop(uid, None)
                self.avatar_assets.pop(uid, None)
            else:
                return await interaction.followup.send('You are not in this game, join up!', ephemeral=True)
            if joining and self.participant_goal is not None and len(self.players) >= self.participant_goal:
                await self.begin_game()
            else:
                await self.refresh_messages()
            await interaction.followup.send('You have joined. Time to get rowdy!' if joining else 'Uh oh, you left the game and left Kylie at the altar!', ephemeral=True)

    @discord.ui.button(label='Join', style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_player(interaction, True)

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.secondary)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_player(interaction, False)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        async with self.lock:
            if not self.authorized(interaction.user):
                return await interaction.followup.send('Excuse me, only Vice Admins can start the game!', ephemeral=True)
            if self.state != 'Lobby open':
                return await interaction.followup.send('This lobby is closed, sorry boo.', ephemeral=True)
            if len(self.players) < 2:
                return await interaction.followup.send('Hold your horses! At least two players must join first.', ephemeral=True)
            await self.begin_game()
            await interaction.followup.send('The game is starting!', ephemeral=True)

    async def begin_game(self):
        # Both callers hold the lobby lock, so manual and automatic start cannot race.
        if self.state != 'Lobby open' or len(self.players) < 2:
            return
        self.state = 'Game running'
        await self.refresh_messages(active=False)
        self.stop()
        self.task = asyncio.create_task(self.run_game())

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await cancel_session(interaction, self)

    @discord.ui.button(label='Repost Registry', style=discord.ButtonStyle.secondary)
    async def repost(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        async with self.lock:
            if self.state != 'Lobby open':
                return await interaction.followup.send('This lobby is closed.', ephemeral=True)
            png = await asyncio.to_thread(render_lobby, ROOT / MODE_IMAGES[self.mode], self.mode)
            attachment = discord.File(BytesIO(png), filename=MODE_IMAGES[self.mode])
            try:
                message = await self.channel.send(embed=self.embed(), view=self, file=attachment,
                                                  **lobby_role_ping(interaction.guild))
            finally:
                attachment.close()
            self.messages.append(message)
            self.message = message
            await interaction.followup.send('Lobby reposted with the current participants!', ephemeral=True)

    async def on_timeout(self):
        async with self.lock:
            if self.state != 'Lobby open':
                return
            self.state = 'Lobby expired'
            self.release()
            try:
                await self.refresh_messages(active=False)
            except discord.HTTPException:
                pass

    async def on_error(self, interaction, error, item):
        report_error('Lobby action failed. Scream for Kylie!', error)
        sender = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        await sender('That action failed. Check the bot permissions and try again. If all help is lost, scream for Kylie!', ephemeral=True)

    async def run_game(self):
        try:
            game = Game(self.players.copy())
            await self.channel.send('The doors are locked. The flirting is questionable. Such good boys and girls, submitting to Kylie. Let the games begin!')
            async def read_avatar(uid):
                try:
                    return uid, await asyncio.wait_for(self.avatar_assets[uid].read(), timeout=10)
                except (discord.HTTPException, asyncio.TimeoutError, KeyError, OSError):
                    return uid, None
            avatars = dict(await asyncio.gather(*(read_avatar(uid) for uid in self.players)))
            while len(game.alive) > 1:
                await asyncio.sleep(ROUND_DELAY if game.round else 5)
                lines = game.step()
                for index, event in enumerate(game.events, 1):
                    label = 'Unexpected death' if event['kind'] == 'unexpected' else 'Battle'
                    embed = discord.Embed(title=f'⚔ ROUND {game.round} ━ {label.upper()} {index}', description=event['text'], color=0xBE428B)
                    png = await asyncio.to_thread(render_card, event, self.profiles, avatars, game.round)
                    filename = f'round-{game.round}-event-{index}.png'
                    embed.set_image(url=f'attachment://{filename}')
                    attachment = discord.File(BytesIO(png), filename=filename)
                    try:
                        await self.channel.send(embed=embed, file=attachment)
                    finally:
                        attachment.close()
                    await asyncio.sleep(EVENT_DELAY)
                quiet = lines[len(game.events):]
                embed = discord.Embed(title=f'✦ ROUND {game.round} ━ SURVIVORS ✦', description='\n\n'.join(quiet) or 'The arena grows quieter.', color=0xBE428B)
                for offset in range(0, len(game.alive), 35):
                    embed.add_field(name=f'Survivors: {len(game.alive)}' if offset == 0 else 'Survivors continued',
                        value=' '.join(f'<@{p}>' for p in game.alive[offset:offset+35]), inline=False)
                await self.channel.send(embed=embed)
            winner = game.alive[0]
            champion_png = await asyncio.to_thread(render_winner, self.profiles.get(winner, 'Champion'), avatars.get(winner), game.round, game.kills[winner])
            champion = discord.Embed(title='🏆 THE ARENA HAS A CHAMPION 🏆',
                description=f'<@{winner}> outlasted {len(self.players)-1} opponents!', color=0xFFD166)
            champion.set_image(url='attachment://champion.png')
            winner_file = discord.File(BytesIO(champion_png), filename='champion.png')
            try:
                await self.channel.send(embed=champion, file=winner_file)
            finally:
                winner_file.close()
            await asyncio.sleep(EVENT_DELAY)
            awards = game.awards()
            mode_name = {
                'classic': 'Classic',
                'sexes': 'Battle of the Sexes',
                'winner': 'Winner Flashes',
                'world': 'North America vs. the World',
            }[self.mode]
            lines = [f'# 🏆 VICE AFTER DARK ARENA 🏆 - {mode_name}\n## ✦ FINAL RESULTS ✦']
            tagged = set()
            for title, ids in awards.items():
                if title.startswith('Most eliminations') or title == 'Survived without a kill':
                    continue
                if title in {'First death', 'Unexpected deaths', 'Survived without a kill'}:
                    continue
                lines.append(f'**{title}:** ' + (', '.join(f'<@{p}>' for p in ids) or 'None this game'))
                tagged.update(ids)
            if self.mode == 'classic':
                targets = list(dict.fromkeys(game.deaths[:1] + game.unexpected))
                if targets:
                    lines.append('**MODE | Classic • Flash ya hoes:** ' + ', '.join(f'<@{p}>' for p in targets)
                        + ' — you died first or died by suicide!')
                    tagged.update(targets)
            if self.mode == 'world':
                targets = opposing_players(game.alive[0], self.players, self.region_roles)
                if targets:
                    lines.append('**MODE | North America vs. the World:** ' + ', '.join(f'<@{p}>' for p in targets)
                        + ' — the other side won! Show us what they are missing.')
                    tagged.update(targets)
                else:
                    lines.append('**MODE | North America vs. the World:** Oh shit... no opposing participants qualified, or the winner has roles on both or neither side. Kylie fucked up and must flash!')
            if self.mode in ('sexes', 'winner'):
                winner = game.alive[0]
                targets = []
                if self.mode == 'winner':
                    targets = [winner]
                else:
                    winner_roles = self.teams.get(winner, set())
                    if len(winner_roles) == 1:
                        opposite = {'She/Her'} if winner_roles == {'He/Him'} else {'He/Him'}
                        targets = [p for p in self.players if self.teams.get(p) == opposite]
                if targets:
                    lines.append('**MODE | Battle of the Sexes:** ' + ', '.join(f'<@{p}>' for p in targets)
                        + ' — time to flash, babe!')
                    tagged.update(targets)
                else:
                    lines.append('**Unable to complete dare** We get it, timing is not always great. Join us in the next round!')
            # Split before Discord's 2,000 character message limit.
            chunks = ['']
            for line in lines:
                if len(chunks[-1]) + len(line) + 1 > 1900:
                    chunks.append('')
                chunks[-1] += line + '\n'
            mentions = discord.AllowedMentions(users=[discord.Object(id=p) for p in tagged], roles=False, everyone=False)
            for chunk in chunks:
                await self.channel.send(chunk, allowed_mentions=mentions)
            self.state = 'Finished'
        except asyncio.CancelledError:
            raise
        except Exception as error:
            report_error('Game stopped', error)
            try:
                await self.channel.send('The game stopped because of an error. Check permissions, scream for Kylie, then start a new lobby.')
            except discord.HTTPException:
                pass
        finally:
            self.release()


async def cancel_session(interaction, lobby):
    await interaction.response.defer(ephemeral=True)
    async with lobby.lock:
        if not lobby.authorized(interaction.user):
            return await interaction.followup.send('Excuse me, only Vice Admin can cancel.', ephemeral=True)
        lobby.state = 'Cancelled'
        if lobby.task:
            lobby.task.cancel()
            try:
                await lobby.task
            except asyncio.CancelledError:
                pass
        lobby.release()
        try:
            await lobby.refresh_messages(active=False)
        except discord.HTTPException:
            pass
        await interaction.followup.send('Game cancelled. Type /game start to begin a new game. If there are issues, let Kylie know.', ephemeral=True)
        await lobby.channel.send('Well, damn. This game has been cancelled!')


@group.command(name='create', description='Open a lobby to start a game. Time to get rowdy!')
@app_commands.describe(mode='Vice Admin can select an optional mode', participant_goal='Vice Admin only: auto-start at this many joined players (2–80); omit for manual start')
@app_commands.choices(mode=[
    app_commands.Choice(name='Classic', value='classic'),
    app_commands.Choice(name='Battle of the Sexes', value='sexes'),
    app_commands.Choice(name='Winner Flashes', value='winner'),
    app_commands.Choice(name='North America vs. the World', value='world'),
])
async def create(interaction: discord.Interaction, mode: str = 'classic', participant_goal: app_commands.Range[int, 2, 80] | None = None):
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message('Use a server text channel.', ephemeral=True)
    if participant_goal is not None and not any(role.name == 'Vice Admin' for role in interaction.user.roles):
        return await interaction.response.send_message('Only the Vice Admin role can set a participant goal.', ephemeral=True)
    if mode != 'classic':
        if not manager(interaction.user):
            return await interaction.response.send_message('Vice Admin role is required to select dare modes.', ephemeral=True)
        if not interaction.channel.is_nsfw():
            return await interaction.response.send_message('Dare modes require an age-restricted text channel.', ephemeral=True)
    permissions = interaction.channel.permissions_for(interaction.guild.me)
    if not (permissions.view_channel and permissions.send_messages and permissions.embed_links and permissions.attach_files):
        return await interaction.response.send_message('I need View Channel, Send Messages, Embed Links, and Attach Files here.', ephemeral=True)
    if interaction.channel_id in sessions:
        return await interaction.response.send_message('Kylie says RELAX! This channel already has a game. Use /game cancel to stop it.', ephemeral=True)
    lobby = Lobby(interaction, mode, participant_goal)
    sessions[interaction.channel_id] = lobby
    try:
        await interaction.response.defer(thinking=True)
        lobby_png = await asyncio.to_thread(render_lobby, ROOT / MODE_IMAGES[mode], mode)
        arena_image = discord.File(BytesIO(lobby_png), filename=MODE_IMAGES[mode])
        try:
            lobby.message = await interaction.followup.send(embed=lobby.embed(), view=lobby, file=arena_image, wait=True,
                                                           **lobby_role_ping(interaction.guild))
            # Use bot-authenticated edits so the 24-hour lobby outlives the interaction token.
            lobby.message = lobby.channel.get_partial_message(lobby.message.id)
            lobby.messages.append(lobby.message)
        finally:
            arena_image.close()
    except Exception:
        lobby.release()
        raise


@group.command(name='cancel', description='Well, damn. This game has been cancelled!')
async def cancel(interaction: discord.Interaction):
    lobby = sessions.get(interaction.channel_id)
    if not lobby:
        return await interaction.response.send_message('Whoopsie daisy, there is no active game here!', ephemeral=True)
    await cancel_session(interaction, lobby)


@client.tree.error
async def command_error(interaction, error):
    original = report_error('Command failed', error)
    if isinstance(original, FileNotFoundError):
        message = 'A mode image is missing. Put arena-classic.png, arena-sexes.png, and arena-winner.png beside bot.py, then retry.'
    elif isinstance(original, discord.Forbidden):
        message = 'Discord denied access. Check View Channel, Send Messages, Embed Links, and Attach Files in this channel.'
    elif isinstance(original, discord.NotFound) and original.code == 10062:
        message = 'Discord expired this interaction. Retry the command and check that only one copy of the bot is running.'
    else:
        message = f'The command failed ({type(original).__name__}). The bot window now shows the full error details.'
    sender = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
    try:
        await sender(message, ephemeral=True)
    except discord.HTTPException:
        logging.error('Could not deliver the error message to Discord.')


if __name__ == '__main__':
    client.run(CONFIG['token'])
