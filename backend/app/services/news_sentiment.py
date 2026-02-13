"""新闻情绪分析服务

从 Yahoo Finance 获取股票相关新闻，使用关键词 NLP 进行情绪评分。
"""

import logging
import re
from datetime import datetime, timezone

import httpx

from app.models.stock import NewsItem, NewsSentiment, Sentiment

logger = logging.getLogger(__name__)

# ── 双语情绪词典 ────────────────────────────────────────────────

POSITIVE_WORDS_EN = {
    # 强正面 (权重 2)
    "surge": 2, "soar": 2, "skyrocket": 2, "boom": 2, "breakout": 2,
    "record high": 2, "all-time high": 2, "beat expectations": 2,
    "blowout": 2, "blockbuster": 2, "massive growth": 2,
    # 正面 (权重 1)
    "buy": 1, "upgrade": 1, "bullish": 1, "rally": 1, "gain": 1,
    "rise": 1, "jump": 1, "climb": 1, "growth": 1, "profit": 1,
    "revenue growth": 1, "outperform": 1, "beat": 1, "strong": 1,
    "positive": 1, "optimistic": 1, "recovery": 1, "rebound": 1,
    "upside": 1, "opportunity": 1, "innovation": 1, "breakthrough": 1,
    "dividend": 1, "buyback": 1, "expand": 1, "partner": 1,
    "approve": 1, "launch": 1, "success": 1, "exceed": 1,
    "momentum": 1, "demand": 1, "confident": 1, "robust": 1,
}

NEGATIVE_WORDS_EN = {
    # 强负面 (权重 2)
    "crash": 2, "plunge": 2, "collapse": 2, "bankrupt": 2, "fraud": 2,
    "scandal": 2, "layoff": 2, "recession": 2, "default": 2,
    "miss expectations": 2, "downgrade": 2,
    # 负面 (权重 1)
    "sell": 1, "bearish": 1, "decline": 1, "drop": 1, "fall": 1,
    "loss": 1, "risk": 1, "warn": 1, "warning": 1, "cut": 1,
    "slash": 1, "weak": 1, "negative": 1, "concern": 1, "fear": 1,
    "uncertainty": 1, "volatility": 1, "lawsuit": 1, "investigation": 1,
    "probe": 1, "fine": 1, "penalty": 1, "debt": 1, "delay": 1,
    "miss": 1, "underperform": 1, "struggle": 1, "trouble": 1,
    "threat": 1, "tariff": 1, "sanction": 1, "inflation": 1,
    "slowdown": 1, "contraction": 1, "overvalued": 1,
}

POSITIVE_WORDS_JP = {
    "上昇": 1, "急騰": 2, "最高値": 2, "好決算": 2, "増収": 1,
    "増益": 1, "上方修正": 2, "買い": 1, "強気": 1, "回復": 1,
    "反発": 1, "成長": 1, "拡大": 1, "好調": 1, "堅調": 1,
    "増配": 1, "自社株買い": 1, "提携": 1, "新製品": 1, "承認": 1,
}

NEGATIVE_WORDS_JP = {
    "下落": 1, "急落": 2, "暴落": 2, "安値": 1, "減収": 1,
    "減益": 1, "下方修正": 2, "売り": 1, "弱気": 1, "懸念": 1,
    "リスク": 1, "不正": 2, "不祥事": 2, "リストラ": 2, "赤字": 1,
    "訴訟": 1, "調査": 1, "罰金": 1, "債務": 1, "延期": 1,
    "不振": 1, "低迷": 1, "円安": 1, "関税": 1, "制裁": 1,
}

POSITIVE_WORDS_ZH = {
    "上涨": 1, "暴涨": 2, "飙升": 2, "创新高": 2, "利好": 2,
    "超预期": 2, "增长": 1, "盈利": 1, "上调": 1, "买入": 1,
    "看涨": 1, "反弹": 1, "突破": 1, "扩张": 1, "合作": 1,
    "创新": 1, "获批": 1, "发布": 1, "回购": 1, "分红": 1,
}

NEGATIVE_WORDS_ZH = {
    "下跌": 1, "暴跌": 2, "崩盘": 2, "利空": 2, "不及预期": 2,
    "亏损": 1, "下调": 1, "卖出": 1, "看跌": 1, "裁员": 2,
    "丑闻": 2, "欺诈": 2, "诉讼": 1, "罚款": 1, "债务": 1,
    "风险": 1, "担忧": 1, "衰退": 1, "通胀": 1, "制裁": 1,
}


def _score_text(text: str) -> float:
    """对文本进行情绪评分，返回 [-1.0, 1.0] 区间的分值。"""
    text_lower = text.lower()
    pos_score = 0
    neg_score = 0

    # 英文词典
    for word, weight in POSITIVE_WORDS_EN.items():
        if word in text_lower:
            pos_score += weight
    for word, weight in NEGATIVE_WORDS_EN.items():
        if word in text_lower:
            neg_score += weight

    # 日文词典
    for word, weight in POSITIVE_WORDS_JP.items():
        if word in text:
            pos_score += weight
    for word, weight in NEGATIVE_WORDS_JP.items():
        if word in text:
            neg_score += weight

    # 中文词典
    for word, weight in POSITIVE_WORDS_ZH.items():
        if word in text:
            pos_score += weight
    for word, weight in NEGATIVE_WORDS_ZH.items():
        if word in text:
            neg_score += weight

    total = pos_score + neg_score
    if total == 0:
        return 0.0

    # 归一化到 [-1, 1]
    raw = (pos_score - neg_score) / total
    return max(-1.0, min(1.0, raw))


def _score_to_sentiment(score: float) -> Sentiment:
    if score > 0.15:
        return Sentiment.POSITIVE
    elif score < -0.15:
        return Sentiment.NEGATIVE
    return Sentiment.NEUTRAL


# ── Yahoo Finance 新闻获取 ──────────────────────────────────────

YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"


def _fetch_news_yahoo(symbol: str) -> list[dict]:
    """从 Yahoo Finance 搜索 API 获取新闻。"""
    try:
        resp = httpx.get(
            YAHOO_SEARCH_URL,
            params={
                "q": symbol,
                "newsCount": 15,
                "quotesCount": 0,
                "listsCount": 0,
                "enableFuzzyQuery": "false",
            },
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                ),
            },
            timeout=10.0,
        )
        if resp.status_code != 200:
            logger.warning(f"Yahoo news search HTTP {resp.status_code} for {symbol}")
            return []

        data = resp.json()
        return data.get("news", [])

    except Exception as e:
        logger.error(f"Yahoo news fetch failed for {symbol}: {e}")
        return []


def _parse_yahoo_news(raw_items: list[dict]) -> list[dict]:
    """解析 Yahoo 新闻搜索结果。"""
    items = []
    for item in raw_items:
        title = item.get("title", "")
        if not title:
            continue

        publisher = item.get("publisher", "Unknown")
        link = item.get("link", "")

        # 解析时间戳
        pub_ts = item.get("providerPublishTime")
        if pub_ts:
            try:
                pub_dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc)
                pub_str = pub_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pub_str = ""
        else:
            pub_str = ""

        items.append({
            "title": title,
            "source": publisher,
            "published_at": pub_str,
            "url": link,
        })

    return items


# ── 公开接口 ────────────────────────────────────────────────────

class NewsSentimentAnalyzer:
    """新闻情绪分析器"""

    def analyze(self, symbol: str) -> NewsSentiment | None:
        """获取并分析股票相关新闻的情绪。"""
        raw_news = _fetch_news_yahoo(symbol)
        parsed = _parse_yahoo_news(raw_news)

        if not parsed:
            logger.info(f"未找到 {symbol} 的相关新闻")
            return NewsSentiment(
                symbol=symbol,
                overall_score=0.0,
                overall_sentiment=Sentiment.NEUTRAL,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                news=[],
                analyzed_at=datetime.now(timezone.utc),
            )

        news_items: list[NewsItem] = []
        scores: list[float] = []
        pos_count = 0
        neg_count = 0
        neu_count = 0

        for item in parsed:
            score = _score_text(item["title"])
            sentiment = _score_to_sentiment(score)
            scores.append(score)

            if sentiment == Sentiment.POSITIVE:
                pos_count += 1
            elif sentiment == Sentiment.NEGATIVE:
                neg_count += 1
            else:
                neu_count += 1

            news_items.append(NewsItem(
                title=item["title"],
                source=item["source"],
                published_at=item["published_at"],
                url=item["url"],
                sentiment=sentiment,
                score=round(score, 2),
            ))

        overall = sum(scores) / len(scores) if scores else 0.0

        return NewsSentiment(
            symbol=symbol,
            overall_score=round(overall, 2),
            overall_sentiment=_score_to_sentiment(overall),
            positive_count=pos_count,
            negative_count=neg_count,
            neutral_count=neu_count,
            news=news_items,
            analyzed_at=datetime.now(timezone.utc),
        )


news_sentiment_analyzer = NewsSentimentAnalyzer()
