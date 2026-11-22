from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.platform.astr_message_event import AstrMessageEvent

from .core.config import PluginConfig
from .core.model import LotteryError
from .core.service import LotteryService
from .core.utils import get_nickname


class LotteryPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config)
        self.service = LotteryService(self.cfg)

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("开启抽奖")
    async def start_lottery(self, event: AstrMessageEvent):
        error = self.service.start_activity(event.get_group_id())
        if error == LotteryError.ACTIVITY_EXISTS:
            yield event.plain_result("该群已有进行中的抽奖活动")
        elif error == LotteryError.INVALID_PRIZE_CONFIG:
            yield event.plain_result("奖项配置无效，请检查档位、权重和数量")
        else:
            yield event.plain_result("本群的抽奖活动已开启")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.command("抽奖")
    async def draw_lottery(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        result = self.service.draw(
            event.get_group_id(),
            user_id,
            await get_nickname(event, user_id),
        )
        error_messages = {
            LotteryError.ACTIVITY_NOT_FOUND: "该群没有抽奖活动",
            LotteryError.ACTIVITY_INACTIVE: "抽奖活动未开启",
            LotteryError.ALREADY_PARTICIPATED: "您已经参与过本次抽奖",
        }
        if result.error:
            yield event.plain_result(error_messages[result.error])
        elif result.prize:
            yield event.plain_result(
                f"🎉 恭喜您中了{result.prize.level}: {result.prize.name}"
            )
        else:
            yield event.plain_result("很遗憾，您未中奖")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("关闭抽奖")
    async def stop_lottery(self, event: AstrMessageEvent):
        error = self.service.stop_activity(event.get_group_id())
        if error == LotteryError.ACTIVITY_NOT_FOUND:
            yield event.plain_result("该群没有抽奖活动")
        elif error == LotteryError.ACTIVITY_INACTIVE:
            yield event.plain_result("抽奖活动已经停止")
        else:
            yield event.plain_result("抽奖活动已停止")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("重置抽奖")
    async def reset_lottery(self, event: AstrMessageEvent):
        error = self.service.delete_activity(event.get_group_id())
        yield event.plain_result(
            "当前无抽奖可重置"
            if error == LotteryError.ACTIVITY_NOT_FOUND
            else "本群抽奖已清空，可重新开启"
        )

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.command("抽奖状态")
    async def lottery_status(self, event: AstrMessageEvent):
        status = self.service.get_status(event.get_group_id())
        if not status:
            yield event.plain_result("当前群聊没有抽奖活动")
            return

        lines = [
            f"📊 本群抽奖活动{'进行中' if status.active else '已结束'}",
            f"参与 {status.participant_count} 人　中奖 {status.winner_count} 人",
            "🎁 奖品剩余：",
        ]
        lines.extend(
            f"{prize.level} {prize.name}：{prize.remaining}/{prize.total}"
            for prize in status.prizes
        )
        yield event.plain_result("\n".join(lines))

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.command("中奖名单")
    async def winner_list(self, event: AstrMessageEvent):
        status = self.service.get_status(event.get_group_id())
        if not status:
            yield event.plain_result("当前群聊没有抽奖活动")
            return
        if not status.winners_by_level:
            yield event.plain_result("暂无中奖者")
            return

        lines = ["🏆 中奖名单："]
        lines.extend(
            f"{level}：{'、'.join(names)}"
            for level, names in status.winners_by_level.items()
        )
        yield event.plain_result("\n".join(lines))
