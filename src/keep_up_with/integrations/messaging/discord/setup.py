from __future__ import annotations

from urllib.parse import urlencode

import httpx

from keep_up_with.integrations.base import MessagingSetupContext, MessagingSetupResult

API = "https://discord.com/api/v10"
ADMINISTRATOR = 1 << 3
BOT_TOKEN_ENV = "DISCORD_BOT_TOKEN"


def configure(ctx: MessagingSetupContext) -> MessagingSetupResult:
    ui = ctx.ui
    current_token = ctx.env(BOT_TOKEN_ENV)

    ui.header("Discord")
    if current_token:
        ui.info("Discord bot token is already set.")
        token = current_token
        token_changed = False
        if ui.confirm("Override bot token?", default=False):
            token = ui.prompt("Bot token", secret=True) or current_token
            token_changed = token != current_token
            if token_changed:
                ctx.set_env(BOT_TOKEN_ENV, token)
    else:
        ui.info("Create a Discord application and bot, then enable Message Content Intent.")
        token = prompt_required(ui, "Bot token", secret=True)
        token_changed = True
        ctx.set_env(BOT_TOKEN_ENV, token)

    current_server_id = str(ctx.current.get("server_id") or "")
    should_check_bot = bool(token and (token_changed or not current_server_id))
    bot = fetch_bot(token) if should_check_bot else {}
    if bot:
        ui.success(f"Found bot: {bot.get('username')} ({bot.get('id')})")
        if token_changed and current_server_id:
            ui.header("Invite")
            ui.info(invite_url(str(bot.get("application_id") or "")))
            ui.pause("Invite the bot to your private message space, then press Enter")
    elif should_check_bot and token:
        ui.warning("Could not verify the bot token. Continuing with manual IDs.")

    ui.header("User")
    user_id = str(ctx.current.get("user_id") or "")
    show_user(ui, token, user_id)
    ui.info("Enable Discord Developer Mode, then right-click yourself and copy User ID.")
    user_id = prompt_required(ui, "Your Discord user ID", user_id)

    ui.header("Server")
    server_id = current_server_id
    reset_space_default = False
    if server_id:
        show_guild(ui, token, server_id)
        server_id = ui.prompt("message space ID", server_id)
    else:
        ui.info("Keep Up With works best in a new private server it can organize.")
        server_kind = ui.select(
            "Server",
            [
                ui.Choice(
                    "New private message space",
                    "new",
                    "recommended",
                ),
                ui.Choice(
                    "Existing server",
                    "existing",
                    "advanced",
                ),
            ],
            "new",
        )
        reset_space_default = server_kind == "new"
        if server_kind == "new":
            ui.info("Create a new message space, invite Keep Up With, then continue.")
            if bot:
                ui.info(invite_url(str(bot.get("application_id") or "")))
            ui.pause("Press Enter after Keep Up With has joined the new server")
        server_id = choose_guild(ui, token) if token else ""
    if not server_id:
        ui.info("Right-click your private message space and copy Server ID.")
        server_id = prompt_required(ui, "message space ID")

    return MessagingSetupResult(
        settings={
            "integration": "discord",
            "server_id": server_id,
            "user_id": user_id,
        },
        reset_space_default=reset_space_default,
    )


def prompt_required(ui, message: str, default: str = "", *, secret: bool = False) -> str:
    while True:
        value = ui.prompt(message, default, secret=secret)
        if value:
            return value
        ui.warning(f"{message} is required.")


def choose_guild(ui, token: str) -> str:
    guilds = fetch_guilds(token)
    if len(guilds) == 1:
        guild = guilds[0]
        ui.success(f"Using server: {guild.get('name')}")
        return str(guild["id"])
    if not guilds:
        return ""
    choices = [
        ui.Choice(
            label=str(guild.get("name") or guild.get("id")),
            value=str(guild["id"]),
            description=str(guild.get("id") or ""),
        )
        for guild in guilds
        if guild.get("id")
    ]
    return ui.select("Choose the server Keep Up With should use", choices)


def show_user(ui, token: str, user_id: str) -> None:
    if not token or not user_id:
        return
    user = fetch_user(token, user_id)
    if user:
        ui.info(f"Current user: {user.get('name')} ({user.get('id')})")


def show_guild(ui, token: str, guild_id: str) -> None:
    if not token or not guild_id:
        return
    guild = fetch_guild(token, guild_id)
    if guild:
        ui.info(f"Current server: {guild.get('name')} ({guild.get('id')})")


def fetch_bot(token: str) -> dict[str, str]:
    try:
        user = get(token, "/users/@me")
        app = get(token, "/oauth2/applications/@me")
    except httpx.HTTPError:
        return {}
    if not isinstance(user, dict) or not isinstance(app, dict):
        return {}
    return {
        "id": str(user.get("id", "")),
        "username": str(user.get("username", "")),
        "application_id": str(app.get("id", "")),
    }


def fetch_user(token: str, user_id: str) -> dict[str, str]:
    try:
        response = get(token, f"/users/{user_id}")
    except httpx.HTTPError:
        return {}
    if not isinstance(response, dict):
        return {}
    username = str(response.get("username") or "")
    discriminator = str(response.get("discriminator") or "")
    return {
        "id": str(response.get("id", "")),
        "name": (
            f"{username}#{discriminator}"
            if discriminator and discriminator != "0"
            else username
        ),
    }


def fetch_guild(token: str, guild_id: str) -> dict[str, str]:
    try:
        response = get(token, f"/guilds/{guild_id}")
    except httpx.HTTPError:
        return {}
    if not isinstance(response, dict):
        return {}
    return {
        "id": str(response.get("id", "")),
        "name": str(response.get("name", "")),
    }


def fetch_guilds(token: str) -> list[dict[str, str]]:
    try:
        response = get(token, "/users/@me/guilds")
    except httpx.HTTPError:
        return []
    if not isinstance(response, list):
        return []
    return [
        {"id": str(item.get("id", "")), "name": str(item.get("name", ""))}
        for item in response
        if isinstance(item, dict)
    ]


def invite_url(application_id: str) -> str:
    return "https://discord.com/oauth2/authorize?" + urlencode(
        {
            "client_id": application_id,
            "permissions": str(ADMINISTRATOR),
            "scope": "bot",
        }
    )


def get(token: str, path: str) -> dict | list:
    response = httpx.get(
        f"{API}{path}",
        headers={"Authorization": f"Bot {token}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
