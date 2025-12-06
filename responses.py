"""
CopyManga API 响应模型
"""

from dataclasses import dataclass, field
from typing import Any

from astrbot.api import logger


@dataclass
class LoginRespData:
    """登录响应"""

    token: str
    user_id: str
    username: str
    nickname: str
    avatar: str
    datetime_created: str
    ticket: int
    reward_ticket: int
    downloads: int
    vip_downloads: int
    reward_downloads: int
    scy_answer: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoginRespData":
        """从字典创建LoginRespData对象"""
        return cls(
            token=data.get("token", ""),
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            nickname=data.get("nickname", ""),
            avatar=data.get("avatar", ""),
            datetime_created=data.get("datetime_created", ""),
            ticket=data.get("ticket", 0),
            reward_ticket=data.get("reward_ticket", 0),
            downloads=data.get("downloads", 0),
            vip_downloads=data.get("vip_downloads", 0),
            reward_downloads=data.get("reward_downloads", 0),
            scy_answer=data.get("scy_answer", ""),
        )


@dataclass
class UserProfileRespData:
    """用户信息响应"""

    user_id: str
    username: str
    nickname: str
    avatar: str
    downloads: int
    vip_downloads: int
    day_downloads: int
    day_downloads_refresh: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserProfileRespData":
        """从字典创建UserProfileRespData对象"""
        return cls(
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            nickname=data.get("nickname", ""),
            avatar=data.get("avatar", ""),
            downloads=data.get("downloads", 0),
            vip_downloads=data.get("vip_downloads", 0),
            day_downloads=data.get("day_downloads", 0),
            day_downloads_refresh=data.get("day_downloads_refresh", ""),
        )


@dataclass
class ComicInSearchRespData:
    """搜索结果中的漫画"""

    name: str
    alias: str
    path_word: str
    cover: str
    author: list[dict[str, str]]
    popular: int


@dataclass
class Pagination:
    """分页信息"""

    total: int
    limit: int
    offset: int


@dataclass
class SearchRespData:
    """搜索响应"""

    comics: list[ComicInSearchRespData]
    pagination: Pagination

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchRespData":
        """从字典创建SearchRespData对象"""
        comics = []
        for comic_data in data["list"]:
            comics.append(
                ComicInSearchRespData(
                    name=comic_data["name"],
                    alias=comic_data["alias"],
                    path_word=comic_data["path_word"],
                    cover=comic_data["cover"],
                    author=comic_data["author"],
                    popular=comic_data["popular"],
                )
            )

        # 处理pagination信息
        # 直接从data中获取total，因为API返回的pagination.total可能不准确
        total = data.get("total", data.get("pagination", {}).get("total", len(comics)))

        # 如果total为0但实际有结果，使用更合理的估算值
        actual_count = len(comics)
        if total <= 0 and actual_count > 0:
            # 计算合理的total值：实际返回数量 * 5 + 随机值，确保总页数合理
            total = actual_count * 5 + 10
            logger.warning(
                f"API返回total为0但实际有{actual_count}条结果，使用估算total: {total}"
            )

        # 获取limit和offset
        limit = data.get("limit", data.get("pagination", {}).get("limit", 20))
        offset = data.get("offset", data.get("pagination", {}).get("offset", 0))

        # 创建pagination对象
        pagination = Pagination(total=total, limit=limit, offset=offset)

        return cls(comics=comics, pagination=pagination)


@dataclass
class ComicInGetComicRespData:
    """获取漫画详情中的漫画"""

    name: str
    alias: str
    path_word: str
    cover: str
    author: list[dict[str, str]]
    theme: list[dict[str, str]]
    brief: str
    status: dict[str, str]
    region: dict[str, str]
    last_chapter: dict[str, str]
    popular: int


@dataclass
class GetComicRespData:
    """获取漫画详情响应"""

    comic: ComicInGetComicRespData
    groups: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GetComicRespData":
        """从字典创建GetComicRespData对象"""
        comic_data = data.get("comic", {})
        comic = ComicInGetComicRespData(
            name=comic_data.get("name", ""),
            alias=comic_data.get("alias", ""),
            path_word=comic_data.get("path_word", ""),
            cover=comic_data.get("cover", ""),
            author=comic_data.get("author", []),
            theme=comic_data.get("theme", []),
            brief=comic_data.get("brief", ""),
            status=comic_data.get("status", {}),
            region=comic_data.get("region", {}),
            last_chapter=comic_data.get("last_chapter", {}),
            popular=comic_data.get("popular", 0),
        )

        return cls(comic=comic, groups=data.get("groups", {}))


@dataclass
class ChapterInGetChaptersRespData:
    """章节列表中的章节"""

    uuid: str
    name: str
    index: int
    count: int
    size: int
    datetime_created: str


@dataclass
class GetChaptersRespData:
    """获取章节列表响应"""

    list: list[ChapterInGetChaptersRespData]
    total: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GetChaptersRespData":
        """从字典创建GetChaptersRespData对象"""
        chapters = []
        for chapter_data in data.get("list", []):
            chapters.append(
                ChapterInGetChaptersRespData(
                    uuid=chapter_data.get("uuid", ""),
                    name=chapter_data.get("name", ""),
                    index=chapter_data.get("index", 0),
                    count=chapter_data.get("count", 0),
                    size=chapter_data.get("size", 0),
                    datetime_created=chapter_data.get("datetime_created", ""),
                )
            )

        return cls(list=chapters, total=data.get("total", 0))


@dataclass
class ContentInGetChapterRespData:
    """章节内容中的图片"""

    url: str
    page: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentInGetChapterRespData":
        """从字典创建ContentInGetChapterRespData对象"""
        return cls(url=data.get("url", ""), page=int(data.get("page", 0)))


@dataclass
class ChapterInGetChapterRespData:
    """获取章节详情中的章节"""

    uuid: str
    name: str
    index: int
    count: int
    size: int
    datetime_created: str
    contents: list[ContentInGetChapterRespData]
    words: list[int] = field(default_factory=list)  # 章节字数统计，用于排序
    is_long: bool = False  # 是否为长篇章节


@dataclass
class GetChapterRespData:
    """获取章节详情响应"""

    comic: dict[str, Any]
    chapter: ChapterInGetChapterRespData

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GetChapterRespData":
        """从字典创建GetChapterRespData对象"""
        chapter_data = data.get("chapter", {})
        contents = []

        # 获取内容列表
        raw_contents = chapter_data.get("contents", [])

        # 处理内容列表
        for content_data in raw_contents:
            # 创建ContentInGetChapterRespData对象
            content = ContentInGetChapterRespData.from_dict(content_data)
            contents.append(content)

        # 获取words字段，用于排序
        words = chapter_data.get("words", [])

        # 按照原始项目的排序方式，使用words字段排序
        if words and len(words) == len(contents):
            # 如果有words字段且长度匹配，按照words字段排序
            # 参考原始项目download_manager.rs的排序逻辑
            contents_with_words = list(zip(contents, words))
            # 按照words值排序
            contents_with_words.sort(key=lambda x: x[1])
            # 重新提取contents
            contents = [content for content, _ in contents_with_words]
        else:
            # 如果没有words字段或长度不匹配，按照page字段排序
            contents.sort(key=lambda x: x.page)

        chapter = ChapterInGetChapterRespData(
            uuid=chapter_data.get("uuid", ""),
            name=chapter_data.get("name", ""),
            index=chapter_data.get("index", 0),
            count=chapter_data.get("count", 0),
            size=chapter_data.get("size", 0),
            datetime_created=chapter_data.get("datetime_created", ""),
            contents=contents,
            words=words,
            is_long=chapter_data.get("is_long", False),
        )

        return cls(comic=data.get("comic", {}), chapter=chapter)
