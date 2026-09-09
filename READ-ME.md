# After Dark Arena — setup guide

An original Discord survival game with suggestive comedy. Players voluntarily join with a button; fights run automatically. No AI subscription is required. This is a first version inspired by the gameplay you described, not a full PixxieBot clone.

## 1. Set up your Discord application

Open https://discord.com/developers/applications and select your application.

* **Bot:** choose **Reset Token** and copy the token privately. Do not send it in chat or publish it. Leave privileged intents disabled; this bot does not need them.
* **Installation:** enable **Guild Install**. Choose **Discord Provided Link**. Under Guild Install settings, add `bot` and `applications.commands`. Select **View Channels**, **Send Messages**, **Embed Links**, and **Attach Files**. Administrator permission is unnecessary.
* Open the install link, select your server, and authorize the bot. You need permission to manage the server.

The normal application setup is sufficient for this single-server starter. Follow Discord's prompts if it requests any account verification.

## 2. Copy your server ID

In the regular Discord app, open **User Settings → Advanced → Developer Mode** and enable it. Right-click your server icon and choose **Copy Server ID**. This is different from your application ID.

## 3. Start on Windows

1. If using the ZIP, extract the entire folder first.
2. Install Python 3.11 or newer from https://www.python.org/downloads/ if you do not already have it. Enable the Python PATH option if offered.
3. Double-click **START.bat**. It creates an isolated environment and installs the Discord library. The initial setup needs internet access.
4. On first launch, Notepad opens `config.json`. Replace `PASTE_BOT_TOKEN_HERE` with your private token and `PASTE_SERVER_ID_HERE` with the server ID. Keep the quotation marks. Save and close Notepad.
5. Wait for **Ready as ...** in the bot window. Keep that window open.

`config.json` contains a secret. Do not upload it or share a ZIP of your configured folder. If the token is exposed, reset it in the Developer Portal and replace it locally.

## 4. Play

In a server text channel, enter **/game create**. Everyone, including the host if participating, clicks **Join**. The roster updates automatically. **Leave** removes a player before the game starts.

The host or a member with **Manage Server** can click **Start** once 2–40 people join. A new round appears every 12 seconds. Each round has eliminations, sometimes with a quiet interlude. The last survivor wins.

Results tag the winner, first death, unexpected deaths, top eliminators (including ties), runner-up, and a winner who survived without a kill. If an award has no qualifying player, it says None. Names in round narration do not send notifications. Final tags allow notifications, subject to each user's Discord settings.

Use **/game cancel** to stop a running game. The host, a **Vice Admin**, or a server manager can start or cancel. One game can run in each text channel; different channels can play independently. Lobbies expire after 24 hours without a lobby-button interaction. Keep the bot running for the lobby to remain available; restarting still clears active lobbies.

The opening lobby includes your VICE After Dark Arena image, bundled as `arena-start.png`. Keep this file beside `bot.py` when updating or moving the bot. The bot needs **Attach Files** permission to display it.

## Vice Admin modes

Create a server role named exactly **Vice Admin** and assign it only to your game managers. The bot checks this role on each management action; Manage Server also grants these controls. Role names are case-sensitive.

Managers can choose the `mode` option on **/game create**:

* **Classic:** regular survival and awards.
* **Battle of the Sexes:** if the winner joined with exactly the **He/Him** role, participating players who joined with exactly **She/Her** receive an optional fictional flash dare. The reverse applies to a She/Her winner.
* **Winner Flashes:** the winner receives the optional fictional flash dare.

Dare modes require an age-restricted text channel. The lobby discloses the mode before anyone joins; clicking Join confirms 18+ participation and opting into a text-only dare. Players may decline. The bot never requests photos or real exposure. Modes cannot change after a lobby is created; cancel and recreate to choose another.

Only joined players are eligible for dare tags, including eliminated participants. Both-role and neither-role players can play and win normally, but are excluded from the opposing-role dare grouping; a both-role or neither-role winner skips that dare. Roles are captured when each player joins. Pronoun roles are used only as game teams, not to infer gender.

## Customize and operate

### Avatar battle cards

Each battle has its own image: two Discord display avatars facing off with handcuffs between them. The eliminated player's avatar is darkened and greyed out. Unexpected deaths get a separate square portrait card. Event narration stays below the card title, with a survivor summary after each round. Animated avatars use a still frame; unavailable avatars use a neutral silhouette. Pictures and display names are captured for the current game, with no avatar files saved to disk.

**Updating an existing copy:** stop the bot, extract the updated ZIP into its folder, and replace the program files. Preserve your private `config.json`. Run START.bat again to install the new Pillow image dependency, and enable **Attach Files** for the bot in the game channel. No extra privileged intents are needed.

* Change `round_seconds` in `config.json` to any number from 3 to 120, then restart.
* Edit the event lists in `engine.py` to add original scenarios. Preserve `{a}` and `{b}` placeholders and keep events short. DUELS eliminate `{b}` and credit `{a}`; ACCIDENTS eliminate `{b}` without a killer. QUIET events do not affect outcomes.
* Closing the window, computer sleep, or a restart stops games. State is in memory; interrupted games do not resume, and old buttons become inactive. Start a fresh lobby after restarting. For 24/7 operation, deploy this folder on an always-on host, install requirements, provide a private config.json, and run `python bot.py` under a process manager.
* This starter has no persistent leaderboard, saved game history, teams, inventory, or interactive combat choices.

## Troubleshooting

* **No /game command:** check the server ID, confirm installation included `applications.commands`, and restart Discord after the bot prints Ready.
* **Login failure:** reset the bot token and replace the token in config.json.
* **Missing Access / Forbidden:** check that the bot is installed in the configured server and has the four channel permissions above. Channel-specific overrides can block it.
* **Invalid JSON:** keep values in quotation marks as shown in config.example.json, and keep commas between fields.
* **Buttons fail after a restart:** old lobbies cannot resume. Create a new one.

## Verification

Run `python -m unittest -v` in this folder to simulate 1,000 complete games and validate winner, death, and elimination accounting. Real Discord behavior must also be checked after connecting your token: join with two accounts, test duplicate Join and Leave, start, wait for results, then test cancellation.

References: [Discord setup](https://docs.discord.com/developers/quick-start/getting-started), [discord.py interactions](https://discordpy.readthedocs.io/en/stable/interactions/api.html).
