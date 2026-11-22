from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.utils.astrbot_path import get_astrbot_plugin_data_path


class PluginConfig:
    """Manage lottery plugin configuration and paths."""

    _plugin_name = "astrbot_plugin_lottery"

    def __init__(self, config: AstrBotConfig):
        self._config = config
        self.data_dir = Path(get_astrbot_plugin_data_path()) / self._plugin_name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.lottery_data_file = self.data_dir / "lottery_data.json"
        self.plugin_dir = Path(__file__).resolve().parent.parent
        self.default_prizes_file = self.plugin_dir / "default_prizes.json"

        if not config.get("prize_entries"):
            config["prize_entries"] = json.loads(
                self.default_prizes_file.read_text(encoding="utf-8")
            )
            config.save_config()

    @property
    def prize_entries(self) -> list[dict[str, Any]]:
        return self._config["prize_entries"]

    @property
    def no_prize_weight(self) -> int:
        return self._config["no_prize_weight"]
