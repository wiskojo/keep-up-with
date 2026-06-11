from __future__ import annotations

import asyncio
import importlib.resources as resources
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, set_key

from keep_up_with.cli.user import ui
from keep_up_with.core.config import (
    KeepUpWithConfig,
    KeepUpWithPaths,
    KeepUpWithSettings,
    load_config,
    write_config,
)
from keep_up_with.integrations.base import (
    DataIntegration,
    MessagingIntegration,
    MessagingSetupContext,
    SpaceResetPreview,
    SpaceChannel,
    SpacePlan,
    SpaceSection,
)
from keep_up_with.integrations.registry import (
    available_data_integrations,
    available_messaging_integrations,
    messaging_client,
)


def run_setup(paths: KeepUpWithPaths) -> None:
    ui.header("keep-up-with setup")
    ensure_dirs(paths)
    reset_space_default = setup_messaging(paths)
    setup_integrations(paths)
    presets = setup_keep_up_with(paths)
    setup_space(paths, presets, reset_default=reset_space_default)
    finish_workspace(paths)
    finish_workflow(paths)
    print()
    ui.success("keep-up-with is ready.")


@dataclass(frozen=True)
class KeepUpWithPreset:
    name: str
    integrations: dict[str, dict[str, list[str]]]
    sections: list[SpaceSection]
    channels: list[SpaceChannel]


def ensure_dirs(paths: KeepUpWithPaths) -> None:
    for path in (
        paths.home,
        paths.workspace,
        paths.logs,
        paths.run,
    ):
        path.mkdir(parents=True, exist_ok=True)
    paths.env.touch(mode=0o600, exist_ok=True)


def write_default_config(paths: KeepUpWithPaths, *, messaging: dict) -> None:
    write_config(paths, KeepUpWithSettings.model_validate(default_config(messaging)))


def default_config(messaging: dict) -> dict:
    return {
        "app": {
            "thread_name": "Main",
            "codex_socket": "~/.codex/app-server-control/app-server-control.sock",
        },
        "messaging": messaging,
        "integrations": {
            integration.name: integration.default_config()
            for integration in sorted(
                available_data_integrations(),
                key=lambda item: item.name,
            )
        },
    }


def write_default_workspace(paths: KeepUpWithPaths) -> None:
    write_workspace_files(paths)
    ensure_managed_workflow(paths)


def write_workspace_files(paths: KeepUpWithPaths) -> None:
    files = {
        "USER.md": "# User",
        "MEMORY.md": "# Memory",
    }
    for name, text in files.items():
        path = paths.workspace / name
        if not path.exists():
            path.write_text(text + "\n")


def finish_workspace(paths: KeepUpWithPaths) -> None:
    write_workspace_files(paths)
    ui.header("Workspace")
    ui.info("Local AI work: USER.md, MEMORY.md, story folders, notes, drafts, assets.")
    ui.info("Reset deletes this workspace and recreates the starter files.")
    if dangerous_confirm(
        "Reset workspace?",
        "This deletes every file in the keep-up-with workspace directory and recreates AGENTS.md, USER.md, MEMORY.md, and the managed keep-up-with workflow.",
        "RESET WORKSPACE",
    ):
        reset_workspace(paths)


def finish_workflow(paths: KeepUpWithPaths) -> None:
    if not managed_workflow_needs_sync(paths):
        return
    ui.header("Workflow")
    ui.info("AGENTS.md plus the keep-up-with deep-dive skill.")
    ui.info("Update replaces managed workflow files with the packaged version.")
    ensure_managed_workflow(paths)


def reset_workspace(paths: KeepUpWithPaths) -> None:
    shutil.rmtree(paths.workspace, ignore_errors=True)
    paths.workspace.mkdir(parents=True, exist_ok=True)
    write_default_workspace(paths)
    ui.success("workspace reset.")


def ensure_managed_workflow(paths: KeepUpWithPaths) -> None:
    items = managed_workflow_paths(paths)
    ensure_managed_sources(items)
    missing = [(source, target) for source, target in items if not target.exists()]
    changed = [
        (source, target)
        for source, target in items
        if target.exists() and not same_resource(source, target)
    ]
    if missing:
        for source, target in missing:
            copy_resource(source, target)
        ui.success("Installed keep-up-with workflow.")
    if not changed:
        return
    ui.warning("The workspace keep-up-with workflow differs from the packaged version.")
    if ui.confirm("Update keep-up-with workflow?", default=False):
        for source, target in changed:
            remove_target(target)
            copy_resource(source, target)


def managed_workflow_needs_sync(paths: KeepUpWithPaths) -> bool:
    items = managed_workflow_paths(paths)
    ensure_managed_sources(items)
    return any(
        not target.exists() or not same_resource(source, target)
        for source, target in items
    )


def managed_workflow_paths(paths: KeepUpWithPaths):
    source = resources.files("keep_up_with.resources").joinpath("workspace_template")
    return [
        (source / "AGENTS.md", paths.workspace / "AGENTS.md"),
        (
            source / "skills" / "keep-up-with",
            paths.workspace / ".agents" / "skills" / "keep-up-with",
        ),
    ]


def ensure_managed_sources(items) -> None:
    for source, _target in items:
        if not source.is_file() and not source.is_dir():
            raise RuntimeError("managed keep-up-with workflow is missing from the package")


def same_resource(source, target: Path) -> bool:
    if source.is_dir():
        return target.is_dir() and same_resource_tree(source, target)
    return target.is_file() and target.read_bytes() == source.read_bytes()


def copy_resource(source, target: Path) -> None:
    if source.is_dir():
        copy_resource_tree(source, target)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def remove_target(target: Path) -> None:
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink(missing_ok=True)


def copy_resource_tree(source, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            copy_resource_tree(item, destination)
        else:
            destination.write_bytes(item.read_bytes())


def same_resource_tree(source, target: Path) -> bool:
    source_files = resource_files(source)
    target_files = {
        item.relative_to(target).as_posix(): item.read_bytes()
        for item in target.rglob("*")
        if item.is_file()
    }
    return source_files == target_files


def resource_files(source, prefix: str = "") -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for item in source.iterdir():
        path = f"{prefix}/{item.name}" if prefix else item.name
        if item.is_dir():
            files.update(resource_files(item, path))
        else:
            files[path] = item.read_bytes()
    return files


def setup_messaging(paths: KeepUpWithPaths) -> bool:
    config = load_existing_config(paths)
    integration = choose_messaging_integration(config)
    if integration.setup is None:
        raise RuntimeError(f"{integration.name} does not support setup")
    current = current_messaging_settings(config, integration)
    result = integration.setup(
        MessagingSetupContext(
            paths=paths,
            current=current,
            env_values=env_values(paths),
            ui=ui,
        )
    )
    messaging = result.settings
    messaging["integration"] = integration.name
    write_messaging_config(paths=paths, config=config, messaging=messaging)
    return result.reset_space_default


def choose_messaging_integration(config: KeepUpWithConfig | None) -> MessagingIntegration:
    integrations = sorted(
        available_messaging_integrations(), key=lambda item: item.name
    )
    if not integrations:
        raise RuntimeError("no messaging integrations are registered")
    current = config.messaging().integration if config else ""
    if len(integrations) == 1:
        return integrations[0]
    selected = ui.select(
        "Messaging",
        [
            ui.Choice(
                label=integration.name,
                value=integration.name,
                description="current" if integration.name == current else "",
            )
            for integration in integrations
        ],
        current or integrations[0].name,
    )
    return next(
        integration for integration in integrations if integration.name == selected
    )


def current_messaging_settings(
    config: KeepUpWithConfig | None,
    integration: MessagingIntegration,
) -> dict:
    if config is None or config.messaging().integration != integration.name:
        return {}
    return config.messaging().model_dump(mode="json")


def load_existing_config(paths: KeepUpWithPaths) -> KeepUpWithConfig | None:
    if not paths.config.exists():
        return None
    return load_config(paths)


def env_values(paths: KeepUpWithPaths) -> dict[str, str]:
    return {
        key: value
        for key, value in dotenv_values(paths.env).items()
        if value is not None
    }


def write_messaging_config(
    *,
    paths: KeepUpWithPaths,
    config: KeepUpWithConfig | None,
    messaging: dict,
) -> None:
    if config is None:
        write_default_config(paths, messaging=messaging)
        return
    current = config.messaging().model_dump(mode="json")
    if current == messaging:
        return
    updated = config.settings.model_dump(mode="json")
    updated["messaging"] = messaging
    write_config(paths, KeepUpWithSettings.model_validate(updated))


def setup_integrations(paths: KeepUpWithPaths) -> None:
    config = load_config(paths)
    integrations = sorted(available_data_integrations(), key=lambda item: item.name)
    current = {
        integration.name
        for integration in integrations
        if config.integration_enabled(integration.name)
    }
    selected = ui.multiselect(
        "Integrations",
        [
            ui.Choice(
                label=integration.name,
                value=integration.name,
                description=integration_hint(integration),
            )
            for integration in integrations
        ],
        current,
    )
    for integration in integrations:
        if integration.name in selected and integration.name not in current:
            enable_connector(paths, integration)
        elif integration.name in selected:
            ensure_connector(paths, integration)
        elif integration.name in current:
            disable_connector(paths, integration)


def enable_connector(paths: KeepUpWithPaths, integration: DataIntegration) -> None:
    config = load_config(paths)
    section = {
        **integration.default_config(enabled=True),
        **config.integration(integration.name),
        "enabled": True,
    }
    write_config(paths, with_integration(config.settings, integration.name, section))
    configure_credentials(
        paths,
        integration.name,
        integration.required_env,
        load_config(paths),
    )
    ui.success(f"{integration.name} enabled.")


def ensure_connector(paths: KeepUpWithPaths, integration: DataIntegration) -> None:
    config = load_config(paths)
    configure_credentials(paths, integration.name, integration.required_env, config)


def setup_keep_up_with(paths: KeepUpWithPaths) -> list[str]:
    config = load_config(paths)
    integrations = sorted(available_data_integrations(), key=lambda item: item.name)
    presets = keep_up_with_presets()
    parameterized = [
        integration
        for integration in integrations
        if config.integration_enabled(integration.name) and integration.parameters
    ]
    selected = selected_presets(config, parameterized, presets)
    choices = [
        *(
            ui.Choice(preset_label(name), f"preset:{name}", "Add sources.")
            for name in presets
        ),
    ]
    selected_values = ui.multiselect(
        "Subscriptions",
        choices,
        selected,
    )
    names = [name for name in presets if f"preset:{name}" in selected_values]
    if not names:
        return []
    for name in names:
        apply_keep_up_with_preset(paths, name, presets[name])
    return names


def has_watch_lists(config: KeepUpWithConfig, integrations: list[DataIntegration]) -> bool:
    return any(
        unique_strings(config.integration(integration.name).get(parameter.name))
        for integration in integrations
        for parameter in integration.parameters
    )


def selected_presets(
    config: KeepUpWithConfig,
    integrations: list[DataIntegration],
    presets: dict[str, KeepUpWithPreset],
) -> set[str]:
    selected = {
        f"preset:{name}"
        for name, preset in presets.items()
        if preset_is_configured(config, preset)
    }
    if selected:
        return selected
    if not integrations or has_watch_lists(config, integrations):
        return set()
    first = next(iter(presets), "")
    return {f"preset:{first}"} if first else set()


def preset_is_configured(
    config: KeepUpWithConfig,
    preset: KeepUpWithPreset,
) -> bool:
    has_enabled_source = False
    for integration, values_by_parameter in preset.integrations.items():
        if not config.integration_enabled(integration):
            continue
        has_enabled_source = True
        section = config.integration(integration)
        for parameter, values in values_by_parameter.items():
            current = set(unique_strings(section.get(parameter)))
            if not set(values).issubset(current):
                return False
    return has_enabled_source


def keep_up_with_presets() -> dict[str, KeepUpWithPreset]:
    loaded: dict[str, KeepUpWithPreset] = {}
    presets = resources.files("keep_up_with.resources").joinpath("presets")
    preset_paths = [
        item
        for item in presets.iterdir()
        if item.name.endswith(".toml")
    ]
    for path in sorted(preset_paths, key=lambda item: item.name):
        value = tomllib.loads(path.read_text())
        integrations: dict[str, dict[str, list[str]]] = {}
        for integration, parameters in value.items():
            if integration == "space":
                continue
            if not isinstance(parameters, dict):
                continue
            fields: dict[str, list[str]] = {}
            for parameter, items in parameters.items():
                values = unique_strings(items)
                if values:
                    fields[str(parameter)] = values
            if fields:
                integrations[str(integration)] = fields
        name = path.name.removesuffix(".toml")
        loaded[name] = KeepUpWithPreset(
            name=name,
            integrations=integrations,
            sections=space_sections(value),
            channels=space_channels(value),
        )
    return loaded


def space_sections(value: dict) -> list[SpaceSection]:
    space = value.get("space")
    if not isinstance(space, dict):
        return []
    sections = space.get("sections")
    if not isinstance(sections, list):
        return []
    rows = [section_fields(section) for section in sections if isinstance(section, dict)]
    return [SpaceSection(key=key, name=name) for key, name in rows if key and name]


def space_channels(value: dict) -> list[SpaceChannel]:
    space = value.get("space")
    if not isinstance(space, dict):
        return []
    channels = space.get("channels")
    if not isinstance(channels, list):
        return []
    rows = [channel_fields(channel) for channel in channels if isinstance(channel, dict)]
    return [
        SpaceChannel(
            key=key,
            name=name,
            section=section,
            description=description,
        )
        for key, name, section, description in rows
        if key and name and section
    ]


def section_fields(section: dict) -> tuple[str, str]:
    return (
        text_field(section, "key", "name"),
        text_field(section, "name", "key"),
    )


def channel_fields(channel: dict) -> tuple[str, str, str, str]:
    return (
        text_field(channel, "key", "name"),
        text_field(channel, "name", "key"),
        text_field(channel, "section"),
        text_field(channel, "description"),
    )


def text_field(value: dict, *names: str) -> str:
    for name in names:
        text = str(value.get(name) or "").strip()
        if text:
            return text
    return ""


def preset_label(name: str) -> str:
    return name.upper() if name == "ai" else name.replace("_", " ").title()


def apply_keep_up_with_preset(
    paths: KeepUpWithPaths,
    name: str,
    preset: KeepUpWithPreset,
) -> None:
    config = load_config(paths)
    sections = dict(config.settings.integrations)
    changed = False
    applied: list[str] = []
    for integration, values_by_parameter in preset.integrations.items():
        if not config.integration_enabled(integration):
            label = preset_label(name)
            ui.warning(
                f"{label} preset includes {integration}, but {integration} is not enabled."
            )
            continue
        section = dict(config.integration(integration))
        for parameter, values in values_by_parameter.items():
            current = unique_strings(section.get(parameter))
            merged = unique_strings([*current, *values])
            if merged != current:
                section[parameter] = merged
                changed = True
        sections[integration] = section
        applied.append(integration)
    if changed:
        write_config(
            paths,
            config.settings.model_copy(update={"integrations": sections}),
        )
    if applied:
        ui.success(f"{preset_label(name)} preset applied: {', '.join(applied)}.")
    else:
        ui.warning(f"No enabled integrations match the {preset_label(name)} preset.")


def setup_space(
    paths: KeepUpWithPaths,
    preset_names: list[str],
    *,
    reset_default: bool,
) -> None:
    presets = keep_up_with_presets()
    plan = space_plan([presets[name] for name in preset_names if name in presets])
    if not plan.sections or not plan.channels:
        return

    config = load_config(paths)
    target = message_space_target(config)
    client = messaging_client(config)
    preview = preview_space_reset(client)
    ui.header("Server layout")
    ui.info(target)
    ui.info("Reset recreates the default channel layout.")
    if preview and preview.default_empty_server:
        ui.info("Fresh default Discord server detected. Resetting layout.")
        asyncio.run(client.apply_space(plan, reset=True))
        ui.success("Server layout is ready.")
        return
    if not ui.confirm("Reset server layout?", default=reset_default):
        return
    if not confirm_space_reset(target, preview):
        return
    asyncio.run(client.apply_space(plan, reset=True))
    ui.success("Server layout is ready.")


def confirm_space_reset(target: str, preview: SpaceResetPreview | None) -> bool:
    if preview is None:
        ui.warning("Could not inspect the current server layout.")
        return ui.confirm(f"Reset {target} anyway?", default=False)
    if preview.default_empty_server or not preview.items:
        return True
    for line in space_delete_lines(preview):
        ui.info(ui.red(line))
    return ui.confirm("Delete these items and reset server layout?", default=False)


def preview_space_reset(client) -> SpaceResetPreview | None:
    try:
        return asyncio.run(client.preview_space_reset())
    except Exception as error:
        ui.warning(f"Could not inspect server layout: {error}")
        return None


def space_delete_lines(preview: SpaceResetPreview) -> list[str]:
    if not preview.items:
        return ["No existing channels or sections."]
    count = len(preview.items)
    noun = "item" if count == 1 else "items"
    return [
        f"Reset will delete {count} existing {noun}:",
        *(f"- {item.kind}: {item.name}" for item in preview.items),
    ]


def message_space_target(config: KeepUpWithConfig) -> str:
    settings = config.messaging().model_dump(mode="json")
    integration = str(settings.get("integration") or "messaging")
    if integration == "discord":
        server_id = str(settings.get("server_id") or "")
        return f"Discord server: {discord_server_label(config, server_id)}"
    return f"Configured messaging platform: {integration}"


def discord_server_label(config: KeepUpWithConfig, server_id: str) -> str:
    if not server_id:
        return "not set"
    try:
        from keep_up_with.integrations.messaging.discord.setup import (
            BOT_TOKEN_ENV,
            lookup_guild,
        )

        token = config.env(BOT_TOKEN_ENV) if config.has_env(BOT_TOKEN_ENV) else ""
        guild = lookup_guild(token, server_id) if token else {}
    except Exception:
        guild = {}
    name = str(guild.get("name") or "").strip()
    guild_id = str(guild.get("id") or server_id).strip()
    return f"{name} ({guild_id})" if name else guild_id


def dangerous_confirm(
    message: str,
    warning: str,
    phrase: str,
    *,
    default: bool = False,
) -> bool:
    while True:
        if not ui.confirm(message, default=default):
            return False
        ui.danger_block(
            "Danger zone",
            [
                f"To continue, type {phrase}.",
                "Press Esc to go back.",
                warning,
                "This cannot be automatically undone.",
            ],
        )
        typed = ui.prompt_cancelable("Confirm phrase")
        if typed is None:
            print()
            continue
        if typed != phrase:
            ui.warning("Cancelled.")
            return False
        return True


def space_plan(presets: list[KeepUpWithPreset]) -> SpacePlan:
    sections = {"general": SpaceSection("general", "General")}
    channels = {
        "general": SpaceChannel(
            key="general",
            name="💬・general",
            section="general",
            description="General updates, questions, and anything that does not fit another channel.",
        )
    }
    for preset in presets:
        for section in preset.sections:
            sections[section.key] = section
        for channel in preset.channels:
            channels[channel.key] = channel
    return SpacePlan(
        sections=list(sections.values()),
        channels=list(channels.values()),
    )


def disable_connector(paths: KeepUpWithPaths, integration: DataIntegration) -> None:
    config = load_config(paths)
    section = {
        **integration.default_config(),
        **config.integration(integration.name),
        "enabled": False,
    }
    write_config(paths, with_integration(config.settings, integration.name, section))
    ui.success(f"{integration.name} disabled.")


def configure_credentials(
    paths: KeepUpWithPaths,
    label: str,
    names: tuple[str, ...] | list[str],
    config: KeepUpWithConfig,
) -> None:
    if not names:
        return
    paths.env.touch(mode=0o600, exist_ok=True)
    missing = [name for name in names if not config.has_env(name)]
    if not missing:
        return
    ui.header(f"{label} credentials")
    for name in missing:
        value = ui.prompt(name, secret=True)
        if value:
            set_key(paths.env.as_posix(), name, value)
            config.env_values[name] = value
        else:
            ui.warning(f"{label} will stay inactive until {name} is set.")


def split_values(value: str) -> list[str]:
    return unique_strings(value.replace("\n", ",").split(","))


def unique_strings(value: object) -> list[str]:
    if isinstance(value, str):
        items = split_values(value) if "," in value else [value]
    elif isinstance(value, list | tuple):
        items = list(value)
    else:
        items = []
    return list(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))


def with_integration(
    settings: KeepUpWithSettings,
    name: str,
    section: dict,
) -> KeepUpWithSettings:
    sections = dict(settings.integrations)
    sections[name] = section
    return settings.model_copy(update={"integrations": sections})


def integration_hint(integration: DataIntegration) -> str:
    parts = [integration.description] if integration.description else []
    env = list(integration.required_env)
    parts.append(f"(env: {', '.join(env) if env else 'none'})")
    return " ".join(parts)
