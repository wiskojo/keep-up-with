from __future__ import annotations

from keep_up_with.integrations.base import DataIntegration, IntegrationParameter
from keep_up_with.integrations.data.web.subscription import items
from keep_up_with.integrations.data.web import tools


def register(registry) -> None:
    registry.add_data(
        DataIntegration(
            name="web",
            description="Web pages and screenshots",
            subscriptions=(items,),
            tools=(tools.download, tools.screenshot),
            parameters=(
                IntegrationParameter(
                    name="feeds",
                    help="https://openai.com/news/rss.xml",
                ),
                IntegrationParameter(
                    name="pages",
                    help="https://www.anthropic.com/engineering",
                ),
            ),
        )
    )
