"""
CopyManga 漫画搜索和下载插件
"""

from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Node, Plain
from astrbot.api.star import Context, Star, register

from .config import Config
from .copymanga_client import CopyMangaClient


@register(
    "copymanga",
    "AstrBot Devs",
    "CopyManga 漫画搜索和下载插件",
    "1.0.0",
    "https://github.com/AstrBotDevs/copymanga-downloader",
)
class CopyMangaPlugin(Star):
    """CopyManga 插件主类"""

    def __init__(self, context: Context, config: dict[str, Any] = None):
        super().__init__(context)
        # 初始化配置
        self.config = Config(config)
        # 初始化 CopyManga 客户端
        self.client = CopyMangaClient(self.config)
        # 初始化会话
        self.sessions = {}

        # 动态应用WebUI配置的命令别名
        self._apply_custom_command_aliases()

    def _apply_custom_command_aliases(self):
        """动态应用WebUI配置的命令别名"""
        import asyncio

        from astrbot.core.star.filter.command import CommandFilter
        from astrbot.core.star.filter.command_group import CommandGroupFilter
        from astrbot.core.star.star_handler import star_handlers_registry

        async def apply_aliases():
            try:
                # 遍历所有命令处理程序
                for handler in star_handlers_registry:
                    # 确保该处理程序属于当前插件
                    if handler.handler_module_path.startswith(
                        "data.plugins.astrbot-plugin-copymanga"
                    ):
                        for filter_ in handler.event_filters:
                            # 处理命令组过滤器
                            if isinstance(filter_, CommandGroupFilter):
                                # 获取原始命令名称
                                original_cmd_name = filter_.group_name

                                # 检查是否有自定义命令名称
                                if original_cmd_name in self.config.command_names:
                                    custom_cmd_name = self.config.command_names[
                                        original_cmd_name
                                    ]

                                    if (
                                        custom_cmd_name
                                        and custom_cmd_name != original_cmd_name
                                    ):
                                        # 更新命令组名称
                                        filter_.group_name = custom_cmd_name

                                        # 清除缓存，重新生成完整命令名称
                                        if hasattr(filter_, "_cmpl_cmd_names"):
                                            filter_._cmpl_cmd_names = None

                                        logger.info(
                                            f"CopyManga 插件：为命令组 {original_cmd_name} 应用自定义名称：{custom_cmd_name}"
                                        )
                            # 处理命令过滤器
                            elif isinstance(filter_, CommandFilter):
                                # 获取原始命令名称
                                original_cmd_name = filter_.command_name

                                # 检查是否有自定义命令名称
                                if original_cmd_name in self.config.command_names:
                                    custom_cmd_name = self.config.command_names[
                                        original_cmd_name
                                    ]

                                    if (
                                        custom_cmd_name
                                        and custom_cmd_name != original_cmd_name
                                    ):
                                        # 更新命令名称
                                        filter_.command_name = custom_cmd_name

                                        # 清除缓存，重新生成完整命令名称
                                        if hasattr(filter_, "_cmpl_cmd_names"):
                                            filter_._cmpl_cmd_names = None

                                        logger.info(
                                            f"CopyManga 插件：为命令 {original_cmd_name} 应用自定义名称：{custom_cmd_name}"
                                        )
            except Exception as e:
                logger.error(f"CopyManga 插件：应用自定义命令别名失败 - {e}")

        # 立即执行异步函数
        asyncio.create_task(apply_aliases())

    async def terminate(self):
        """插件被卸载/停用时调用"""
        await self.client.close()

    # 命令组处理函数，当用户输入命令组名称时，返回帮助信息
    @filter.command_group("copymanga")
    async def copymanga_group(self, event: AstrMessageEvent):
        """CopyManga 命令组，当用户输入命令组名称时返回帮助信息"""
        # 当用户输入命令组名称时，直接返回帮助信息，而不是默认的命令树
        # 调用帮助命令处理函数
        async for result in self.copymanga_direct_command(event):
            yield result

    # 帮助命令处理函数
    @filter.command("copymanga_help", alias={"帮助"})
    async def copymanga_direct_command(self, event: AstrMessageEvent):
        """处理help命令，返回精简命令列表和使用流程"""
        # 动态获取所有命令名称
        commands = {
            "login": self.config.command_names.get(
                "copymanga_login", "copymanga_login"
            ),
            "search": self.config.command_names.get(
                "copymanga_search", "copymanga_search"
            ),
            "select_comic": self.config.command_names.get(
                "copymanga_select_comic", "copymanga_select_comic"
            ),
            "select_chapter": self.config.command_names.get(
                "copymanga_select_chapter", "copymanga_select_chapter"
            ),
            "chapter_mode": self.config.command_names.get(
                "copymanga_chapter_mode", "copymanga_chapter_mode"
            ),
            "profile": self.config.command_names.get(
                "copymanga_profile", "copymanga_profile"
            ),
            "config": self.config.command_names.get(
                "copymanga_config", "copymanga_config"
            ),
            "test_api": self.config.command_names.get(
                "copymanga_test_api", "copymanga_test_api"
            ),
            "next": self.config.command_names.get("copymanga_next", "copymanga_next"),
            "prev": self.config.command_names.get("copymanga_prev", "copymanga_prev"),
            "jump": self.config.command_names.get("copymanga_jump", "copymanga_jump"),
            "next_page": self.config.command_names.get(
                "copymanga_next_page", "copymanga_next_page"
            ),
            "prev_page": self.config.command_names.get(
                "copymanga_prev_page", "copymanga_prev_page"
            ),
            "help": self.config.command_names.get("copymanga_help", "copymanga_help"),
        }

        # 构建精简的命令列表
        message = "📖 CopyManga 漫画插件帮助信息\n\n"
        message += "💡 基本使用流程：\n"
        message += f"  1. 搜索漫画：/{commands['search']} 关键词\n"
        message += f"  2. 选择漫画：/{commands['select_comic']} 序号\n"
        message += f"  3. 选择章节：/{commands['select_chapter']} 序号\n"
        message += f"  4. 翻页阅读：/{commands['next']} /{commands['prev']}\n"
        message += f"  5. 跳页阅读：/{commands['jump']} 页码\n\n"

        message += "📚 可用命令：\n\n"
        message += "  🔍 搜索相关：\n"
        message += f"    /{commands['search']} <关键词> [页码] - 搜索漫画\n"
        message += f"    /{commands['next_page']} - 搜索结果下一页\n"
        message += f"    /{commands['prev_page']} - 搜索结果上一页\n\n"

        message += "  📖 阅读相关：\n"
        message += f"    /{commands['select_comic']} <序号> - 选择搜索结果中的漫画\n"
        message += f"    /{commands['select_chapter']} <序号> - 选择章节阅读\n"
        message += f"    /{commands['next']} - 下一页\n"
        message += f"    /{commands['prev']} - 上一页\n"
        message += f"    /{commands['jump']} <页码> - 跳转到指定页码\n"
        message += f"    /{commands['chapter_mode']} [模式] - 切换章节阅读模式\n\n"

        message += "  🔧 配置相关：\n"
        message += f"    /{commands['login']} <用户名> <密码> - 登录 CopyManga 账号\n"
        message += f"    /{commands['profile']} - 查看当前登录用户信息\n"
        message += f"    /{commands['config']} [配置项] [值] - 查看或修改插件配置\n"
        message += f"    /{commands['test_api']} [API域名] - 测试API域名连接\n\n"

        message += "  ❓ 帮助信息：\n"
        message += f"    /{commands['help']} - 查看帮助信息\n\n"

        message += "💡 示例：\n"
        message += f"  - 搜索海贼王：/{commands['search']} 海贼王\n"
        message += f"  - 选择第1个漫画：/{commands['select_comic']} 1\n"
        message += f"  - 选择第5个章节：/{commands['select_chapter']} 5\n"
        message += f"  - 跳转到第10页：/{commands['jump']} 10"

        yield event.plain_result(message)

    # 登录命令
    @copymanga_group.command("login")
    async def login_command(
        self, event: AstrMessageEvent, username: str, password: str
    ):
        """登录 CopyManga 账号

        Args:
            username: 用户名
            password: 密码
        """
        try:
            result = await self.client.login(username, password)

            # 更新配置中的token
            self.config.set_config({"token": result.token})

            yield event.plain_result(f"登录成功，欢迎回来，{result.nickname}！")
        except Exception as e:
            logger.error(f"登录失败：{str(e)}")
            yield event.plain_result(f"登录失败：{str(e)}")

    # 搜索命令
    @copymanga_group.command("search", alias={"搜索漫画"})
    async def search_command(
        self, event: AstrMessageEvent, keyword: str, page: int = 1
    ):
        """搜索 CopyManga 漫画

        Args:
            keyword: 搜索关键词
            page: 页码，默认1
        """
        try:
            result = await self.client.search(keyword, page)

            # 保存搜索结果到会话
            session_key = f"{event.get_sender_id()}"
            if session_key not in self.sessions:
                self.sessions[session_key] = {}

            # 直接使用API返回的分页信息
            total_items = result.pagination.total
            actual_items = len(result.comics)
            items_per_page = result.pagination.limit

            # 确保items_per_page有效
            if items_per_page <= 0:
                items_per_page = self.config.config.get("search_limit", 20)

            # 计算总页数
            total_pages = (total_items + items_per_page - 1) // items_per_page

            # 确保总页数至少为1
            if total_pages < 1:
                total_pages = 1

            logger.info(
                f"搜索结果：关键词={keyword}，页码={page}，实际返回={actual_items}，总条目={total_items}，每页条数={items_per_page}，总页数={total_pages}"
            )

            # 更新会话信息
            session = self.sessions[session_key]
            session["keyword"] = keyword
            session["search_results"] = result.comics
            session["current_page"] = page
            session["total_pages"] = total_pages
            session["total_items"] = total_items

            # 获取配置中的搜索显示限制
            search_display_limit = self.config.config.get("search_display_limit", 10)

            # 构建合并转发消息
            nodes = []

            # 创建内容列表，包含文本和图片
            content_list = [
                Plain(
                    f"🔍 搜索结果 | {keyword} | 第 {page}/{total_pages} 页 | 共 {total_items} 条\n"
                ),
                Plain("-" * 50 + "\n"),
            ]

            # 只显示配置数量的漫画
            displayed_comics = result.comics[:search_display_limit]

            for i, comic in enumerate(displayed_comics):
                # 格式化作者列表，使其更简洁
                authors = (
                    ", ".join([author.get("name", "") for author in comic.author])
                    if comic.author
                    else "未知"
                )

                # 添加漫画基本信息，使用简洁排版
                comic_info = (
                    f"【{(page - 1) * search_display_limit + i + 1}】 {comic.name}\n"
                )
                if comic.alias:
                    comic_info += f"别名：{comic.alias}\n"
                comic_info += f"作者：{authors} | 热度：{comic.popular}\n"

                content_list.append(Plain(comic_info))

                # 添加漫画封面图片
                # 清理图片URL，移除可能的反引号等特殊字符
                cover_url = comic.cover.strip().strip("`")
                content_list.append(Image(cover_url))

                # 添加简洁分隔
                content_list.append(Plain("-" * 50 + "\n"))

            # 如果有更多漫画，显示提示
            if len(result.comics) > search_display_limit:
                content_list.append(
                    Plain(
                        f"... 本页共 {len(result.comics)} 个结果，显示前 {search_display_limit} 个\n"
                    )
                )
                content_list.append(Plain("-" * 50 + "\n"))

            # 构建简洁操作指南
            guide_lines = []
            guide_lines.append("\n📋 操作：")

            # 动态获取命令名称
            select_comic_cmd = self.config.command_names.get(
                "copymanga_select_comic", "copymanga_select_comic"
            )
            prev_page_cmd = self.config.command_names.get(
                "copymanga_prev_page", "copymanga_prev_page"
            )
            next_page_cmd = self.config.command_names.get(
                "copymanga_next_page", "copymanga_next_page"
            )

            guide_lines.append(f"  /{select_comic_cmd} 序号 - 选择漫画")

            # 简化翻页命令提示
            if total_pages > 1:
                if page > 1:
                    guide_lines.append(f"  /{prev_page_cmd} - 上一页")
                if page < total_pages:
                    guide_lines.append(f"  /{next_page_cmd} - 下一页")

            page_hint = "\n".join(guide_lines) + "\n"

            content_list.append(Plain(page_hint))

            # 创建一个包含所有信息和图片的节点
            comics_node = Node(
                uin="123456789",  # 虚拟发送者ID
                name="CopyManga搜索助手",
                content=content_list,
            )
            nodes.append(comics_node)

            # 发送合并转发消息
            yield event.chain_result(nodes)
        except Exception as e:
            logger.error(f"搜索失败：{str(e)}")
            yield event.plain_result(f"搜索失败：{str(e)}")

    # 直接搜索命令（支持别名）
    @filter.command("copymanga_search", alias={"搜索漫画"})
    async def direct_search_command(
        self, event: AstrMessageEvent, keyword: str, page: int = 1
    ):
        """直接搜索 CopyManga 漫画（支持别名）

        Args:
            keyword: 搜索关键词
            page: 页码，默认1
        """
        async for result in self.search_command(event, keyword, page):
            yield result

    # 选择漫画命令
    @copymanga_group.command("select_comic", alias={"选择漫画"})
    async def select_comic_command(
        self,
        event: AstrMessageEvent,
        comic_index: int,
        group_path_word: str = "default",
    ):
        """选择搜索结果中的漫画

        Args:
            comic_index: 漫画序号（从1开始）
            group_path_word: 分组路径标识，默认default
        """
        session_key = f"{event.get_sender_id()}"
        if (
            session_key in self.sessions
            and "search_results" in self.sessions[session_key]
        ):
            search_results = self.sessions[session_key]["search_results"]

            if 1 <= comic_index <= len(search_results):
                selected_comic = search_results[comic_index - 1]
                self.sessions[session_key]["selected_comic"] = selected_comic

                # 获取漫画详情，包括章节分组
                comic_detail = await self.client.get_comic(selected_comic.path_word)
                self.sessions[session_key]["comic_detail"] = comic_detail

                # 自动获取章节列表
                chapters_result = await self.client.get_chapters(
                    selected_comic.path_word, group_path_word
                )
                self.sessions[session_key]["chapters"] = chapters_result.list
                self.sessions[session_key]["selected_group"] = group_path_word

                # 获取当前用户的章节阅读模式
                user_id = event.get_sender_id()
                current_mode = self.config.get_user_chapter_content_mode(user_id)
                mode_name = (
                    "单页发送" if current_mode == "single" else "合并转发整章内容"
                )

                # 构建漫画信息
                message = f"已选择漫画：{selected_comic.name}\n\n"
                message += f"别名：{selected_comic.alias}\n"
                message += f"作者：{[author.get('name', '') for author in selected_comic.author]}\n"
                message += f"当前章节阅读模式：{current_mode}（{mode_name}）\n\n"
                message += "章节列表：\n\n"

                # 显示章节列表
                for i, chapter in enumerate(
                    chapters_result.list[:20]
                ):  # 只显示前20个章节
                    message += f"{i + 1}. {chapter.name}（{chapter.count}页）\n"

                if chapters_result.total > 20:
                    message += f"\n... 共 {chapters_result.total} 个章节，显示前20个\n"

                # 动态获取命令名称
                select_chapter_cmd = self.config.command_names.get(
                    "copymanga_select_chapter", "copymanga_select_chapter"
                )
                chapter_mode_cmd = self.config.command_names.get(
                    "copymanga_chapter_mode", "copymanga_chapter_mode"
                )
                message += f"\n请使用 /{select_chapter_cmd} 序号 选择章节阅读\n"
                message += (
                    f"使用 /{chapter_mode_cmd} <模式> 切换章节阅读模式（single/merge）"
                )

                yield event.plain_result(message)
            else:
                yield event.plain_result(
                    f"序号超出范围！请输入1-{len(search_results)}之间的数字"
                )
        else:
            yield event.plain_result(
                "您还没有搜索漫画，请先使用 /copymanga_search 关键词 搜索漫画"
            )

    # 直接选择漫画命令
    @filter.command("copymanga_select_comic", alias={"选择漫画"})
    async def direct_select_comic_command(
        self,
        event: AstrMessageEvent,
        comic_index: int,
        group_path_word: str = "default",
    ):
        """直接选择搜索结果中的漫画（支持别名）

        Args:
            comic_index: 漫画序号（从1开始）
            group_path_word: 分组路径标识，默认default
        """
        async for result in self.select_comic_command(
            event, comic_index, group_path_word
        ):
            yield result

    # 选择章节命令
    @copymanga_group.command("select_chapter", alias={"选择章节"})
    async def select_chapter_command(
        self, event: AstrMessageEvent, chapter_index: int, forward_all: bool = None
    ):
        """选择章节阅读

        Args:
            chapter_index: 章节序号（从1开始）
            forward_all: 是否合并转发整章内容，默认使用配置项 chapter_content_mode
        """
        session_key = f"{event.get_sender_id()}"
        if (
            session_key in self.sessions
            and "chapters" in self.sessions[session_key]
            and "selected_comic" in self.sessions[session_key]
        ):
            chapters = self.sessions[session_key]["chapters"]
            selected_comic = self.sessions[session_key]["selected_comic"]

            if 1 <= chapter_index <= len(chapters):
                selected_chapter = chapters[chapter_index - 1]

                # 保存选中的章节到会话
                self.sessions[session_key]["selected_chapter"] = selected_chapter

                # 决定是否合并转发整章内容
                # 如果用户显式指定了forward_all，则使用用户指定的值
                # 否则使用用户的章节阅读模式配置
                if forward_all is None:
                    # 使用用户配置项决定
                    user_id = event.get_sender_id()
                    content_mode = self.config.get_user_chapter_content_mode(user_id)
                    forward_all = content_mode == "merge"
                    logger.info(
                        f"使用用户配置 chapter_content_mode: {content_mode}，forward_all: {forward_all}"
                    )

                if forward_all:
                    # 合并转发整章内容
                    async for result in self._forward_chapter(
                        event, selected_comic.path_word, selected_chapter.uuid
                    ):
                        yield result
                else:
                    # 开始阅读选择的章节（单页模式）
                    async for result in self._start_reading(
                        event, selected_comic.path_word, selected_chapter.uuid
                    ):
                        yield result
            else:
                yield event.plain_result(
                    f"序号超出范围！请输入1-{len(chapters)}之间的数字"
                )
        else:
            # 动态获取命令名称
            search_cmd = self.config.command_names.get(
                "copymanga_search", "copymanga_search"
            )
            select_comic_cmd = self.config.command_names.get(
                "copymanga_select_comic", "copymanga_select_comic"
            )
            yield event.plain_result(
                f"请先使用 /{search_cmd} 搜索漫画，/{select_comic_cmd} 选择漫画"
            )

    # 直接选择章节命令
    @filter.command("copymanga_select_chapter", alias={"选择章节"})
    async def direct_select_chapter_command(
        self, event: AstrMessageEvent, chapter_index: int, forward_all: bool = None
    ):
        """直接选择章节阅读（支持别名）

        Args:
            chapter_index: 章节序号（从1开始）
            forward_all: 是否合并转发整章内容，默认使用配置项 chapter_content_mode
        """
        async for result in self.select_chapter_command(
            event, chapter_index, forward_all
        ):
            yield result

    # 用户信息命令
    @copymanga_group.command("profile")
    async def profile_command(self, event: AstrMessageEvent):
        """获取当前登录用户信息"""
        result = await self.client.get_user_profile()

        message = "用户信息：\n\n"
        message += f"用户名：{result.username}\n"
        message += f"昵称：{result.nickname}\n"
        message += f"剩余下载次数：{result.downloads}\n"
        message += f"VIP下载次数：{result.vip_downloads}\n"
        message += f"今日下载次数：{result.day_downloads}\n"

        yield event.plain_result(message)

    # 直接用户信息命令
    @filter.command("copymanga_profile")
    async def direct_profile_command(self, event: AstrMessageEvent):
        """直接获取当前登录用户信息"""
        async for result in self.profile_command(event):
            yield result

    # 切换章节模式命令
    @copymanga_group.command("chapter_mode", alias={"章节模式"})
    async def chapter_mode_command(self, event: AstrMessageEvent, mode: str = None):
        """切换章节阅读模式

        Args:
            mode: 阅读模式，可选值：single（单页发送）、merge（合并转发整章内容），不提供则查看当前模式
        """
        try:
            # 获取用户ID
            user_id = event.get_sender_id()

            # 获取当前用户的章节阅读模式
            current_mode = self.config.get_user_chapter_content_mode(user_id)

            if mode is None:
                # 查看当前模式
                mode_name = (
                    "单页发送" if current_mode == "single" else "合并转发整章内容"
                )
                yield event.plain_result(
                    f"当前章节阅读模式：{current_mode}（{mode_name}）\n\n可用模式：\n- single：单页发送\n- merge：合并转发整章内容\n\n使用命令：/章节模式 <模式> 切换阅读模式"
                )
            else:
                # 验证模式值
                if mode not in ["single", "merge"]:
                    yield event.plain_result(
                        f"无效的模式值：{mode}\n\n可用模式：\n- single：单页发送\n- merge：合并转发整章内容"
                    )
                    return

                # 更新用户的章节阅读模式
                self.config.set_user_chapter_content_mode(user_id, mode)

                # 显示更新结果
                mode_name = "单页发送" if mode == "single" else "合并转发整章内容"
                yield event.plain_result(f"章节阅读模式已更新为：{mode}（{mode_name}）")
        except Exception as e:
            logger.error(f"切换章节模式失败：{str(e)}")
            yield event.plain_result(f"切换章节模式失败：{str(e)}")

    # 直接切换章节模式命令
    @filter.command("copymanga_chapter_mode", alias={"章节模式"})
    async def direct_chapter_mode_command(
        self, event: AstrMessageEvent, mode: str = None
    ):
        """直接切换章节阅读模式（支持别名）

        Args:
            mode: 阅读模式，可选值：single（单页发送）、merge（合并转发整章内容），不提供则查看当前模式
        """
        async for result in self.chapter_mode_command(event, mode):
            yield result

    # 配置命令
    @copymanga_group.command("config")
    async def config_command(
        self, event: AstrMessageEvent, key: str = None, value: str = None
    ):
        """查看或修改 CopyManga 插件配置

        Args:
            key: 配置键
            value: 配置值
        """
        if key is None:
            # 查看所有配置
            config = self.config.get_config()
            message = "当前配置：\n\n"
            for k, v in config.items():
                message += f"{k}: {v}\n"
            yield event.plain_result(message)

        elif value is None:
            # 查看指定配置
            config = self.config.get_config()
            if key in config:
                yield event.plain_result(f"配置 {key} 的值为：{config[key]}")
            else:
                yield event.plain_result(f"配置 {key} 不存在")

        else:
            # 修改配置
            config = self.config.get_config()

            # 验证配置键是否存在
            if key not in config:
                yield event.plain_result(f"配置 {key} 不存在")
                return

            # 更新配置
            new_config = {key: value}

            # 特殊处理数值类型
            if key in [
                "ticket",
                "downloads",
                "vip_downloads",
                "reward_downloads",
                "day_downloads",
            ]:
                try:
                    new_config[key] = int(value)
                except ValueError:
                    yield event.plain_result(f"配置 {key} 必须是数值类型")
                    return

            self.config.set_config(new_config)

            # 如果修改了API域名相关配置，重新初始化客户端
            if key in ["api_domain", "custom_api_domain", "api_domain_mode"]:
                await self.client.close()
                self.client = CopyMangaClient(self.config)

            yield event.plain_result(f"配置 {key} 更新成功，新值为：{value}")

    # 直接配置命令
    @filter.command("copymanga_config")
    async def direct_config_command(
        self, event: AstrMessageEvent, key: str = None, value: str = None
    ):
        """直接查看或修改 CopyManga 插件配置"""
        async for result in self.config_command(event, key, value):
            yield result

    # 测试API命令
    @copymanga_group.command("test_api", alias={"测试API"})
    async def test_api_command(self, event: AstrMessageEvent, api_domain: str = None):
        """测试API域名连接

        Args:
            api_domain: 要测试的API域名，不提供则测试当前配置的域名
        """
        original_domain = self.config.get_api_domain()

        try:
            # 如果提供了API域名，临时修改配置进行测试
            if api_domain:
                # 保存原始配置
                original_mode = self.config.config.get("api_domain_mode", "Default")
                original_custom = self.config.config.get("custom_api_domain", "")

                # 设置临时配置
                if api_domain in [
                    "api.copymanga.site",
                    "api.copymanga.cn",
                    "api.copymanga.net",
                ]:
                    self.config.set_config(
                        {"api_domain": api_domain, "api_domain_mode": "Default"}
                    )
                else:
                    self.config.set_config(
                        {"custom_api_domain": api_domain, "api_domain_mode": "Custom"}
                    )

                # 重新初始化客户端
                await self.client.close()
                self.client = CopyMangaClient(self.config)

            # 测试API连接
            test_url = f"https://{self.config.get_api_domain()}/api/v3/search/comic?limit=1&offset=0&q=test&platform=1"
            yield event.plain_result(
                f"正在测试API域名：{self.config.get_api_domain()}..."
            )

            # 发送一个简单的GET请求进行测试
            session = await self.client._get_session()
            async with session.get(
                test_url, headers=self.client.headers, timeout=30
            ) as resp:
                if resp.status == 200:
                    yield event.plain_result(
                        f"API域名 {self.config.get_api_domain()} 测试成功！"
                    )
                else:
                    yield event.plain_result(
                        f"API域名 {self.config.get_api_domain()} 测试失败，状态码：{resp.status}"
                    )
        except Exception as e:
            yield event.plain_result(
                f"API域名 {self.config.get_api_domain()} 测试失败，错误：{str(e)}"
            )
        finally:
            # 恢复原始配置
            if api_domain:
                self.config.set_config(
                    {
                        "api_domain": original_domain,
                        "api_domain_mode": original_mode,
                        "custom_api_domain": original_custom,
                    }
                )
                # 重新初始化客户端
                await self.client.close()
                self.client = CopyMangaClient(self.config)

    # 直接测试API命令
    @filter.command("copymanga_test_api", alias={"测试API"})
    async def direct_test_api_command(
        self, event: AstrMessageEvent, api_domain: str = None
    ):
        """直接测试API域名连接（支持别名）

        Args:
            api_domain: 要测试的API域名，不提供则测试当前配置的域名
        """
        async for result in self.test_api_command(event, api_domain):
            yield result

    # 阅读命令

    # 下一页命令
    @copymanga_group.command("next", alias={"下一页"})
    async def next_command(self, event: AstrMessageEvent):
        """下一页"""
        session_key = f"{event.get_sender_id()}"
        if session_key in self.sessions and "reading" in self.sessions[session_key]:
            reading_session = self.sessions[session_key]["reading"]
            if reading_session["current_page"] < reading_session["total_pages"] - 1:
                reading_session["current_page"] += 1
                async for result in self._show_page(event, session_key):
                    yield result
            else:
                yield event.plain_result("已经是最后一页了！")
        else:
            # 动态获取命令名称
            search_cmd = self.config.command_names.get(
                "copymanga_search", "copymanga_search"
            )
            select_comic_cmd = self.config.command_names.get(
                "copymanga_select_comic", "copymanga_select_comic"
            )
            select_chapter_cmd = self.config.command_names.get(
                "copymanga_select_chapter", "copymanga_select_chapter"
            )
            yield event.plain_result(
                f"您还没有开始阅读漫画，请使用 /{search_cmd} 搜索漫画，/{select_comic_cmd} 选择漫画，然后使用 /{select_chapter_cmd} 选择章节开始阅读。"
            )

    # 直接下一页命令
    @filter.command("copymanga_next", alias={"下一页"})
    async def direct_next_command(self, event: AstrMessageEvent):
        """直接下一页（支持别名）"""
        async for result in self.next_command(event):
            yield result

    # 上一页命令
    @copymanga_group.command("prev", alias={"上一页"})
    async def prev_command(self, event: AstrMessageEvent):
        """上一页"""
        session_key = f"{event.get_sender_id()}"
        if session_key in self.sessions and "reading" in self.sessions[session_key]:
            reading_session = self.sessions[session_key]["reading"]
            if reading_session["current_page"] > 0:
                reading_session["current_page"] -= 1
                async for result in self._show_page(event, session_key):
                    yield result
            else:
                yield event.plain_result("已经是第一页了！")
        else:
            # 动态获取命令名称
            search_cmd = self.config.command_names.get(
                "copymanga_search", "copymanga_search"
            )
            select_comic_cmd = self.config.command_names.get(
                "copymanga_select_comic", "copymanga_select_comic"
            )
            select_chapter_cmd = self.config.command_names.get(
                "copymanga_select_chapter", "copymanga_select_chapter"
            )
            yield event.plain_result(
                f"您还没有开始阅读漫画，请使用 /{search_cmd} 搜索漫画，/{select_comic_cmd} 选择漫画，然后使用 /{select_chapter_cmd} 选择章节开始阅读。"
            )

    # 直接上一页命令
    @filter.command("copymanga_prev", alias={"上一页"})
    async def direct_prev_command(self, event: AstrMessageEvent):
        """直接上一页（支持别名）"""
        async for result in self.prev_command(event):
            yield result

    # 跳转命令
    @copymanga_group.command("jump", alias={"跳页"})
    async def jump_command(self, event: AstrMessageEvent, page: int):
        """跳转到指定页码

        Args:
            page: 要跳转到的页码
        """
        session_key = f"{event.get_sender_id()}"
        if session_key in self.sessions and "reading" in self.sessions[session_key]:
            reading_session = self.sessions[session_key]["reading"]
            target_page = page - 1  # 转为0-based索引
            if 0 <= target_page < reading_session["total_pages"]:
                reading_session["current_page"] = target_page
                async for result in self._show_page(event, session_key):
                    yield result
            else:
                yield event.plain_result(
                    f"页码超出范围！当前章节共有 {reading_session['total_pages']} 页。"
                )
        else:
            # 动态获取命令名称
            search_cmd = self.config.command_names.get(
                "copymanga_search", "copymanga_search"
            )
            select_comic_cmd = self.config.command_names.get(
                "copymanga_select_comic", "copymanga_select_comic"
            )
            select_chapter_cmd = self.config.command_names.get(
                "copymanga_select_chapter", "copymanga_select_chapter"
            )
            yield event.plain_result(
                f"您还没有开始阅读漫画，请使用 /{search_cmd} 搜索漫画，/{select_comic_cmd} 选择漫画，然后使用 /{select_chapter_cmd} 选择章节开始阅读。"
            )

    # 直接跳转命令
    @filter.command("copymanga_jump", alias={"跳页"})
    async def direct_jump_command(self, event: AstrMessageEvent, page: int):
        """直接跳转到指定页码（支持别名）

        Args:
            page: 要跳转到的页码
        """
        async for result in self.jump_command(event, page):
            yield result

    # 搜索结果下一页命令
    @copymanga_group.command("next_page", alias={"搜索下一页"})
    async def next_page_command(self, event: AstrMessageEvent):
        """搜索结果下一页"""
        session_key = f"{event.get_sender_id()}"
        if (
            session_key in self.sessions
            and "search_results" in self.sessions[session_key]
        ):
            session = self.sessions[session_key]
            if "keyword" in session and "current_page" in session:
                current_page = session["current_page"]
                keyword = session["keyword"]

                try:
                    # 尝试获取下一页结果
                    async for result in self.search_command(
                        event, keyword, current_page + 1
                    ):
                        yield result
                except Exception:
                    # 如果获取失败，可能是已经到了最后一页
                    yield event.plain_result("已经是最后一页了！")
            else:
                yield event.plain_result("请先使用 /copymanga_search 关键词 搜索漫画。")
        else:
            yield event.plain_result("请先使用 /copymanga_search 关键词 搜索漫画。")

    # 直接搜索结果下一页命令
    @filter.command("copymanga_next_page", alias={"搜索下一页"})
    async def direct_next_page_command(self, event: AstrMessageEvent):
        """直接搜索结果下一页（支持别名）"""
        async for result in self.next_page_command(event):
            yield result

    # 搜索结果上一页命令
    @copymanga_group.command("prev_page", alias={"搜索上一页"})
    async def prev_page_command(self, event: AstrMessageEvent):
        """搜索结果上一页"""
        session_key = f"{event.get_sender_id()}"
        if (
            session_key in self.sessions
            and "search_results" in self.sessions[session_key]
        ):
            session = self.sessions[session_key]
            if "keyword" in session and "current_page" in session:
                current_page = session["current_page"]
                keyword = session["keyword"]

                if current_page > 1:
                    # 调用搜索命令，获取上一页结果
                    async for result in self.search_command(
                        event, keyword, current_page - 1
                    ):
                        yield result
                else:
                    yield event.plain_result("已经是第一页了！")
            else:
                yield event.plain_result("请先使用 /copymanga_search 关键词 搜索漫画。")
        else:
            yield event.plain_result("请先使用 /copymanga_search 关键词 搜索漫画。")

    # 直接搜索结果上一页命令
    @filter.command("copymanga_prev_page", alias={"搜索上一页"})
    async def direct_prev_page_command(self, event: AstrMessageEvent):
        """直接搜索结果上一页（支持别名）"""
        async for result in self.prev_page_command(event):
            yield result

    # 合并转发章节内容
    async def _forward_chapter(
        self, event: AstrMessageEvent, comic_path_word: str, chapter_uuid: str
    ):
        """合并转发整章内容

        Args:
            event: 消息事件
            comic_path_word: 漫画路径标识
            chapter_uuid: 章节UUID
        """
        import os

        # 获取章节详情
        result = await self.client.get_chapter(comic_path_word, chapter_uuid)
        chapter = result.chapter
        comic_name = result.comic.get("name", "未知漫画")

        # 确保总页数准确，使用实际内容数量
        actual_total = len(chapter.contents)

        # 获取配置的下载目录
        download_dir = self.config.get_download_dir()

        # 创建有意义的目录结构：download_dir/漫画名称/章节名称/
        # 清理目录名称中的特殊字符
        safe_comic_name = "".join(
            [c for c in comic_name if c.isalnum() or c in "-_ "]
        ).strip()
        safe_chapter_name = "".join(
            [c for c in chapter.name if c.isalnum() or c in "-_ "]
        ).strip()

        # 构建下载目录
        chapter_dir = os.path.join(download_dir, safe_comic_name, safe_chapter_name)

        # 确保下载目录存在
        os.makedirs(chapter_dir, exist_ok=True)

        # 下载所有图片到本地，使用并发下载提高速度
        downloaded_images = []

        # 构建下载任务列表
        download_tasks = []

        for i, content in enumerate(chapter.contents):
            # 构建保存路径
            image_name = f"page_{i + 1}.jpg"
            save_path = os.path.join(chapter_dir, image_name)

            # 如果文件不存在，添加到下载任务列表
            if not os.path.exists(save_path):
                download_tasks.append((i + 1, content.url, save_path))
            else:
                # 文件已经存在，直接添加到已下载列表
                downloaded_images.append(save_path)
                logger.info(f"图片已存在，跳过下载任务: {save_path}")

        # 如果有需要下载的图片，执行下载
        if download_tasks:
            # 并发下载图片，添加错误恢复和重试机制
            import asyncio

            async def download_task(page_num, url, save_path, retry_count=3):
                """单个图片下载任务，带重试机制"""
                for attempt in range(retry_count):
                    try:
                        logger.info(
                            f"开始下载第 {page_num}/{actual_total} 页 (尝试 {attempt + 1}/{retry_count}): {url}"
                        )
                        await self.client.download_image(url, save_path)
                        logger.info(
                            f"完成下载第 {page_num}/{actual_total} 页: {save_path}"
                        )
                        return save_path
                    except Exception as e:
                        logger.error(
                            f"下载第 {page_num}/{actual_total} 页失败 (尝试 {attempt + 1}/{retry_count}): {url}, 错误: {str(e)}"
                        )
                        if attempt < retry_count - 1:
                            # 重试前等待1秒
                            await asyncio.sleep(1)
                return None  # 所有重试都失败，返回None

            # 使用asyncio.gather并发执行下载任务
            logger.info(f"开始并发下载 {len(download_tasks)} 张图片")

            # 限制并发数为10，避免请求过多
            semaphore = asyncio.Semaphore(10)

            async def bounded_download(page_num, url, save_path):
                """带并发限制的下载任务"""
                async with semaphore:
                    return await download_task(page_num, url, save_path)

            # 执行所有下载任务
            download_results = await asyncio.gather(
                *[
                    bounded_download(page_num, url, save_path)
                    for page_num, url, save_path in download_tasks
                ],
                return_exceptions=False,  # 不返回异常，而是由download_task内部处理
            )

            # 过滤出成功下载的图片
            downloaded_images += [
                result for result in download_results if result is not None
            ]

            logger.info(
                f"下载完成，成功 {len(downloaded_images)}/{actual_total} 张图片"
            )
        else:
            logger.info(f"所有图片已存在，无需下载，共 {len(downloaded_images)} 张图片")

        # 如果没有图片，抛出异常
        if not downloaded_images:
            yield event.plain_result(
                "❌ 所有图片下载失败或不存在，请检查网络连接或稍后重试"
            )
            return

        # 创建合并转发消息
        nodes = []

        # 构建章节信息
        content_list = [
            Plain(f"📖 漫画：{comic_name}\n"),
            Plain(f"📄 章节：{chapter.name}\n"),
            Plain(f"📑 页数：{actual_total}\n"),  # 使用实际页数
            Plain(f"💾 本地保存路径：{chapter_dir}\n"),  # 显示本地保存路径
            Plain("=" * 50 + "\n\n"),
        ]

        # 添加所有页的本地图片
        for i, image_path in enumerate(downloaded_images):
            # 使用实际索引和实际总页数
            content_list.append(Plain(f"\n第 {i + 1}/{actual_total} 页\n"))
            content_list.append(Image(image_path))

        # 创建一个包含所有内容的节点
        chapter_node = Node(
            uin="123456789",  # 虚拟发送者ID
            name="CopyManga阅读助手",
            content=content_list,
        )
        nodes.append(chapter_node)

        # 发送合并转发消息
        yield event.chain_result(nodes)

        # 保存阅读状态到会话，以便后续可以继续单页阅读
        session_key = f"{event.get_sender_id()}"
        if session_key not in self.sessions:
            self.sessions[session_key] = {}

        self.sessions[session_key]["reading"] = {
            "comic_path_word": comic_path_word,
            "chapter_uuid": chapter_uuid,
            "chapter": chapter,
            "current_page": 0,  # 从第一页开始
            "total_pages": actual_total,  # 使用实际页数
        }

    # 开始阅读章节
    async def _start_reading(
        self,
        event: AstrMessageEvent,
        comic_path_word: str,
        chapter_uuid: str,
        page: int = 1,
    ):
        """开始阅读漫画章节

        Args:
            event: 消息事件
            comic_path_word: 漫画路径标识
            chapter_uuid: 章节UUID
            page: 起始页码，默认1
        """
        # 获取章节详情
        result = await self.client.get_chapter(comic_path_word, chapter_uuid)

        # 保存阅读状态到会话
        session_key = f"{event.get_sender_id()}"
        if session_key not in self.sessions:
            self.sessions[session_key] = {}

        self.sessions[session_key]["reading"] = {
            "comic_path_word": comic_path_word,
            "chapter_uuid": chapter_uuid,
            "chapter": result.chapter,
            "current_page": page - 1,  # 转为0-based索引
            "total_pages": len(result.chapter.contents),
        }

        # 显示当前页
        async for result in self._show_page(event, session_key):
            yield result

    # 显示当前页
    async def _show_page(self, event: AstrMessageEvent, session_key: str):
        """显示当前页

        Args:
            event: 消息事件
            session_key: 会话密钥
        """
        if session_key in self.sessions and "reading" in self.sessions[session_key]:
            reading_session = self.sessions[session_key]["reading"]
            current_page = reading_session["current_page"]
            total_pages = reading_session["total_pages"]
            chapter = reading_session["chapter"]

            # 获取当前页的图片
            if 0 <= current_page < total_pages:
                image_url = chapter.contents[current_page].url

                # 发送图片和页码信息
                yield event.plain_result(f"第 {current_page + 1}/{total_pages} 页")
                yield event.image_result(image_url)

                # 发送翻页提示
                if total_pages > 1:
                    if current_page == 0:
                        yield event.plain_result("使用 /copymanga_next 查看下一页")
                    elif current_page == total_pages - 1:
                        yield event.plain_result("使用 /copymanga_prev 查看上一页")
                    else:
                        yield event.plain_result(
                            "使用 /copymanga_prev 查看上一页，/copymanga_next 查看下一页，/copymanga_jump 页码 跳转到指定页"
                        )
            else:
                yield event.plain_result("页码超出范围！")
        else:
            yield event.plain_result(
                "您还没有开始阅读漫画，请使用 /copymanga_read 命令开始阅读。"
            )

    def _add_command_aliases(self):
        """动态为命令添加别名"""
        # 命令别名已通过装饰器直接配置，无需动态添加
        logger.info("命令别名已通过装饰器直接配置，无需动态添加")

    # 命令别名已通过装饰器直接配置，无需事件监听器处理
    # AstrBot会自动识别别名命令
