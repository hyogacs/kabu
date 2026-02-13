import type { NewsSentiment as NewsSentimentData } from "../types";

interface Props {
  sentiment: NewsSentimentData;
}

const sentimentLabel: Record<string, string> = {
  POSITIVE: "积极",
  NEGATIVE: "消极",
  NEUTRAL: "中性",
};

const sentimentColor: Record<string, string> = {
  POSITIVE: "var(--green)",
  NEGATIVE: "var(--red)",
  NEUTRAL: "var(--yellow)",
};

const sentimentBg: Record<string, string> = {
  POSITIVE: "var(--green-dim)",
  NEGATIVE: "var(--red-dim)",
  NEUTRAL: "var(--yellow-dim)",
};

export function NewsSentimentPanel({ sentiment }: Props) {
  const total = sentiment.positive_count + sentiment.negative_count + sentiment.neutral_count;
  const scorePct = Math.round(((sentiment.overall_score + 1) / 2) * 100); // map [-1,1] → [0,100]

  return (
    <div className="card">
      <div className="card-title">新闻情绪分析</div>

      {/* Overall sentiment gauge */}
      <div className="sentiment-overview">
        <div className="sentiment-score-row">
          <span
            className="sentiment-badge"
            style={{
              background: sentimentBg[sentiment.overall_sentiment],
              color: sentimentColor[sentiment.overall_sentiment],
            }}
          >
            {sentimentLabel[sentiment.overall_sentiment]}
          </span>
          <div className="sentiment-gauge">
            <div className="sentiment-gauge-bg">
              <div
                className="sentiment-gauge-fill"
                style={{
                  width: `${scorePct}%`,
                  background: `linear-gradient(90deg, var(--red), var(--yellow) 50%, var(--green))`,
                }}
              />
              <div
                className="sentiment-gauge-marker"
                style={{ left: `${scorePct}%` }}
              />
            </div>
            <div className="sentiment-gauge-labels">
              <span>消极</span>
              <span>中性</span>
              <span>积极</span>
            </div>
          </div>
          <span className="sentiment-score-text">
            {sentiment.overall_score > 0 ? "+" : ""}
            {sentiment.overall_score.toFixed(2)}
          </span>
        </div>

        {/* Counts bar */}
        <div className="sentiment-counts">
          <div className="sentiment-count-item">
            <div className="sentiment-count-dot" style={{ background: "var(--green)" }} />
            <span>积极 {sentiment.positive_count}</span>
          </div>
          <div className="sentiment-count-item">
            <div className="sentiment-count-dot" style={{ background: "var(--yellow)" }} />
            <span>中性 {sentiment.neutral_count}</span>
          </div>
          <div className="sentiment-count-item">
            <div className="sentiment-count-dot" style={{ background: "var(--red)" }} />
            <span>消极 {sentiment.negative_count}</span>
          </div>
          <span className="sentiment-total">共 {total} 条新闻</span>
        </div>

        {/* Distribution bar */}
        {total > 0 && (
          <div className="sentiment-bar">
            {sentiment.positive_count > 0 && (
              <div
                className="sentiment-bar-seg positive"
                style={{ width: `${(sentiment.positive_count / total) * 100}%` }}
              />
            )}
            {sentiment.neutral_count > 0 && (
              <div
                className="sentiment-bar-seg neutral"
                style={{ width: `${(sentiment.neutral_count / total) * 100}%` }}
              />
            )}
            {sentiment.negative_count > 0 && (
              <div
                className="sentiment-bar-seg negative"
                style={{ width: `${(sentiment.negative_count / total) * 100}%` }}
              />
            )}
          </div>
        )}
      </div>

      {/* News list */}
      {sentiment.news.length > 0 && (
        <div className="news-list">
          {sentiment.news.map((item, idx) => (
            <a
              key={idx}
              className="news-item"
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <div className="news-item-header">
                <span
                  className="news-sentiment-dot"
                  style={{ background: sentimentColor[item.sentiment] }}
                  title={sentimentLabel[item.sentiment]}
                />
                <span className="news-title">{item.title}</span>
              </div>
              <div className="news-meta">
                <span className="news-source">{item.source}</span>
                {item.published_at && (
                  <span className="news-time">{item.published_at}</span>
                )}
                <span
                  className="news-score"
                  style={{ color: sentimentColor[item.sentiment] }}
                >
                  {item.score > 0 ? "+" : ""}{item.score.toFixed(2)}
                </span>
              </div>
            </a>
          ))}
        </div>
      )}

      {sentiment.news.length === 0 && (
        <div className="empty-state" style={{ padding: 20 }}>
          <p>暂无相关新闻</p>
        </div>
      )}
    </div>
  );
}
