from __future__ import annotations

from keep_up_with.integrations.base import SubscriptionContext, poll_every
from keep_up_with.integrations.data.youtube.client import channel_videos


@poll_every("youtube.videos", default_interval_seconds=900)
def videos(ctx: SubscriptionContext) -> None:
    settings = ctx.settings()
    api_key = ctx.env("YOUTUBE_API_KEY")
    channels = [str(item) for item in settings.get("channels") or [] if str(item).strip()]
    for channel in channels:
        for item in channel_videos(api_key, channel):
            video_id = item.get("video_id")
            if not video_id:
                continue
            actor = item.get("channel_title") or channel or "YouTube"
            item["watch"] = channel
            ctx.emit(
                kind="video",
                external_id=str(video_id),
                summary=f"{actor}: {item.get('title') or 'New video'}",
                refs={"video_id": video_id, "url": item.get("url", "")},
                data=item,
            )
