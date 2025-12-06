"""
CopyManga 错误定义
"""


class CopyMangaError(Exception):
    """CopyManga 基础错误"""

    pass


class RiskControlError(CopyMangaError):
    """风控错误"""

    pass


class NetworkError(CopyMangaError):
    """网络错误"""

    pass
