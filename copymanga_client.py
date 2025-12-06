"""
CopyManga API客户端
"""

import asyncio
import os
import ssl
from typing import Any

import aiohttp

from astrbot.api import logger

from .config import Config
from .errors import CopyMangaError, NetworkError, RiskControlError
from .responses import (
    GetChapterRespData,
    GetChaptersRespData,
    GetComicRespData,
    LoginRespData,
    SearchRespData,
    UserProfileRespData,
)


class CopyMangaClient:
    """CopyManga API客户端"""

    def __init__(self, config: Config):
        self.config = config
        self.session: aiohttp.ClientSession | None = None
        self.headers = {
            "User-Agent": "COPY/3.0.0",
            "Accept": "application/json",
            "version": "2025.08.15",
            "platform": "1",
            "webp": "1",
            "region": "1",
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def close(self):
        """关闭HTTP会话"""
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None:
            # 创建客户端会话，添加SSL证书验证选项和超时设置
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    ssl=False,  # 禁用SSL证书验证，解决部分SSL问题
                    ttl_dns_cache=300,  # DNS缓存时间
                ),
                timeout=aiohttp.ClientTimeout(
                    connect=30,  # 连接超时30秒
                    sock_connect=30,  # socket连接超时30秒
                    sock_read=60,  # socket读取超时60秒
                ),
            )
        return self.session

    async def _request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """发送HTTP请求"""
        retries = 5  # 增加重试次数到5次
        retry_delay = 2  # 增加重试间隔到2秒

        for i in range(retries):
            try:
                session = await self._get_session()

                # 添加默认请求头
                headers = {**self.headers, **kwargs.pop("headers", {})}

                logger.debug(f"发送请求: {method} {url}，参数: {kwargs}")

                async with session.request(
                    method, url, headers=headers, **kwargs
                ) as resp:
                    # 检查响应状态
                    if resp.status == 210:
                        body = await resp.text()
                        raise RiskControlError(body)
                    elif resp.status == 401:
                        body = await resp.text()
                        raise CopyMangaError(f"请求失败，token错误或过期: {body}")
                    elif resp.status != 200:
                        body = await resp.text()
                        raise CopyMangaError(
                            f"请求失败，状态码: {resp.status}, 响应: {body}"
                        )

                    # 解析响应
                    body = await resp.json()
                    if body.get("code") != 200:
                        raise CopyMangaError(
                            f"请求失败，code: {body.get('code')}, 响应: {body}"
                        )

                    return body
            except aiohttp.ClientError as e:
                logger.warning(f"请求异常，正在重试 ({i + 1}/{retries}): {str(e)}")
                if i == retries - 1:
                    raise NetworkError(str(e))
                await asyncio.sleep(retry_delay)  # 重试间隔
            except ssl.SSLError as e:
                logger.warning(f"SSL 错误，正在重试 ({i + 1}/{retries}): {str(e)}")
                if i == retries - 1:
                    raise NetworkError(str(e))
                await asyncio.sleep(retry_delay)  # 重试间隔
            except Exception as e:
                logger.error(f"请求异常: {str(e)}")
                if i == retries - 1:
                    raise
                await asyncio.sleep(retry_delay)  # 重试间隔

    async def login(self, username: str, password: str) -> LoginRespData:
        """登录CopyManga"""
        # 添加详细日志，记录登录参数
        logger.info(f"尝试登录，用户名: {username}, 密码长度: {len(password)} 位")

        # 尝试使用不同的参数名称组合
        # 组合1：使用username参数
        data = {"username": username, "password": password, "source": "freeSite"}

        # 发送请求，使用json格式
        api_domain = self.config.get_api_domain()
        url = f"https://{api_domain}/api/v3/login"

        # 添加详细日志，记录请求信息
        logger.info(f"发送登录请求到: {url}")
        logger.info(f"请求参数: {data}")

        try:
            # 尝试使用json格式发送请求
            resp = await self._request("POST", url, json=data)
            logger.info(f"登录请求成功，响应: {resp}")
        except Exception as e:
            logger.error(f"使用json格式登录失败: {str(e)}")
            logger.info("尝试使用form-data格式重新发送请求...")

            # 组合2：尝试使用form-data格式
            try:
                resp = await self._request("POST", url, data=data)
                logger.info(f"使用form-data格式登录成功，响应: {resp}")
            except Exception as e2:
                logger.error(f"使用form-data格式登录也失败: {str(e2)}")

                # 组合3：尝试使用email作为参数名
                logger.info("尝试使用email作为用户名参数名...")
                data_email = {
                    "email": username,
                    "password": password,
                    "source": "freeSite",
                }

                try:
                    resp = await self._request("POST", url, json=data_email)
                    logger.info(f"使用email参数名登录成功，响应: {resp}")
                except Exception as e3:
                    logger.error(f"使用email参数名登录也失败: {str(e3)}")
                    raise CopyMangaError(f"登录失败，已尝试多种参数组合: {str(e3)}")

        # 解析响应
        results = resp["results"]
        return LoginRespData.from_dict(results)

    async def get_user_profile(self) -> UserProfileRespData:
        """获取用户信息"""
        # 构建请求头
        headers = {"authorization": self.config.get_authorization()}

        # 发送请求
        api_domain = self.config.get_api_domain()
        url = f"https://{api_domain}/api/v3/member/info"
        resp = await self._request("GET", url, headers=headers)

        # 解析响应
        return UserProfileRespData.from_dict(resp["results"])

    async def search(self, keyword: str, page_num: int = 1) -> SearchRespData:
        """搜索漫画"""
        # 从配置中获取搜索结果最大返回数量
        limit = self.config.config.get("search_limit", 20)

        # 构建请求参数
        params = {
            "limit": limit,
            "offset": (page_num - 1) * limit,
            "q": keyword,
            "q_type": "",
            "platform": 1,
        }

        # 发送请求
        api_domain = self.config.get_api_domain()
        url = f"https://{api_domain}/api/v3/search/comic"
        resp = await self._request("GET", url, params=params)

        # 记录API返回的实际结果数量和分页信息
        results = resp["results"]
        actual_count = len(results.get("list", []))
        logger.info(
            f"搜索API返回结果：关键词={keyword}, 请求limit={limit}, 实际返回={actual_count}, 总条目={results.get('pagination', {}).get('total', 0)}"
        )

        # 解析响应
        return SearchRespData.from_dict(results)

    async def get_comic(self, comic_path_word: str) -> GetComicRespData:
        """获取漫画详情"""
        # 构建请求参数
        params = {
            "platform": 1,
        }

        # 发送请求
        api_domain = self.config.get_api_domain()
        url = f"https://{api_domain}/api/v3/comic2/{comic_path_word}"
        resp = await self._request("GET", url, params=params)

        # 解析响应
        return GetComicRespData.from_dict(resp["results"])

    async def get_chapters(
        self,
        comic_path_word: str,
        group_path_word: str,
        limit: int = 100,
        offset: int = 0,
    ) -> GetChaptersRespData:
        """获取章节列表"""
        # 构建请求参数
        params = {
            "limit": limit,
            "offset": offset,
        }

        # 发送请求
        api_domain = self.config.get_api_domain()
        url = f"https://{api_domain}/api/v3/comic/{comic_path_word}/group/{group_path_word}/chapters"
        resp = await self._request("GET", url, params=params)

        # 解析响应
        return GetChaptersRespData.from_dict(resp["results"])

    async def get_group_chapters(
        self, comic_path_word: str, group_path_word: str
    ) -> list[Any]:
        """获取分组的所有章节"""
        # 获取第一页章节
        first_page = await self.get_chapters(
            comic_path_word, group_path_word, limit=100, offset=0
        )
        chapters = first_page.list

        # 计算总页数
        total_pages = (first_page.total + 100 - 1) // 100

        # 并发获取剩余页数
        if total_pages > 1:
            from asyncio import gather

            tasks = []
            for page in range(2, total_pages + 1):
                offset = (page - 1) * 100
                tasks.append(
                    self.get_chapters(
                        comic_path_word, group_path_word, limit=100, offset=offset
                    )
                )

            results = await gather(*tasks)
            for result in results:
                chapters.extend(result.list)

        return chapters

    async def get_chapter(
        self, comic_path_word: str, chapter_uuid: str
    ) -> GetChapterRespData:
        """获取章节详情"""
        # 构建请求参数
        params = {
            "platform": 1,
        }

        # 构建请求头
        headers = {"authorization": self.config.get_authorization()}

        # 发送请求
        api_domain = self.config.get_api_domain()
        url = f"https://{api_domain}/api/v3/comic/{comic_path_word}/chapter2/{chapter_uuid}"
        resp = await self._request("GET", url, params=params, headers=headers)

        # 解析响应
        return GetChapterRespData.from_dict(resp["results"])

    async def download_image(self, url: str, save_path: str) -> None:
        """下载图片到本地

        Args:
            url: 图片URL
            save_path: 保存路径
        """
        # 检查文件是否已经存在，如果存在则跳过下载
        if os.path.exists(save_path):
            logger.info(f"图片已存在，跳过下载: {save_path}")
            return

        session = await self._get_session()

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        try:
            async with session.get(url, headers=self.headers, timeout=60) as resp:
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(await resp.read())
        except Exception as e:
            logger.error(f"下载图片失败: {url}, 错误: {str(e)}")
            raise NetworkError(f"下载图片失败: {str(e)}")
