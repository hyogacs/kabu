import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { Portfolio, HoldingCategory } from "../types";
import { getPortfolio } from "../services/api";

function fmtYen(v: number): string {
  return `¥${v.toLocaleString("ja-JP")}`;
}

function fmtPnl(v: number): string {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toLocaleString("ja-JP")}`;
}

function pnlClass(v: number): string {
  return v >= 0 ? "change-positive" : "change-negative";
}

function pnlPct(pnl: number, cost: number): string {
  if (cost === 0) return "-";
  const pct = (pnl / cost) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(2)}%`;
}

function StockCategoryTable({ cat }: { cat: HoldingCategory }) {
  if (!cat.stocks?.length) return null;
  return (
    <div className="portfolio-category">
      <div className="portfolio-category-header">
        <h3>{cat.category_name}</h3>
        <div className="portfolio-category-summary">
          <span className="portfolio-summary-label">評価額</span>
          <span className="portfolio-summary-value">{fmtYen(cat.total_market_value)}</span>
          {cat.total_pnl != null && (
            <>
              <span className="portfolio-summary-label">損益</span>
              <span className={`portfolio-summary-value ${pnlClass(cat.total_pnl)}`}>
                {fmtPnl(cat.total_pnl)}
              </span>
            </>
          )}
        </div>
      </div>
      <div className="stock-table-container">
        <table className="stock-table">
          <thead>
            <tr>
              <th>コード</th>
              <th>銘柄</th>
              <th>保有数</th>
              <th>取得単価</th>
              <th>現在値</th>
              <th>取得金額</th>
              <th>評価額</th>
              <th>評価損益</th>
              <th>損益率</th>
            </tr>
          </thead>
          <tbody>
            {cat.stocks.map((s) => (
              <tr key={`${cat.category_name}-${s.code}`}>
                <td><span className="symbol-cell">{s.code}</span></td>
                <td><span className="name-cell-portfolio">{s.name}</span></td>
                <td className="volume-cell">{s.quantity.toLocaleString()}</td>
                <td className="price-cell">{fmtYen(s.cost_price)}</td>
                <td className="price-cell">{fmtYen(s.current_price)}</td>
                <td className="volume-cell">{fmtYen(s.cost_total)}</td>
                <td className="price-cell">{fmtYen(s.market_value)}</td>
                <td className={`price-cell ${pnlClass(s.unrealized_pnl)}`}>
                  {fmtPnl(s.unrealized_pnl)}
                </td>
                <td className={`price-cell ${pnlClass(s.unrealized_pnl)}`}>
                  {pnlPct(s.unrealized_pnl, s.cost_total)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FundCategoryTable({ cat }: { cat: HoldingCategory }) {
  if (!cat.funds?.length) return null;
  return (
    <div className="portfolio-category">
      <div className="portfolio-category-header">
        <h3>{cat.category_name}</h3>
        <div className="portfolio-category-summary">
          <span className="portfolio-summary-label">評価額</span>
          <span className="portfolio-summary-value">{fmtYen(cat.total_market_value)}</span>
          {cat.total_pnl != null && (
            <>
              <span className="portfolio-summary-label">損益</span>
              <span className={`portfolio-summary-value ${pnlClass(cat.total_pnl)}`}>
                {fmtPnl(cat.total_pnl)}
              </span>
            </>
          )}
        </div>
      </div>
      <div className="stock-table-container">
        <table className="stock-table">
          <thead>
            <tr>
              <th>ファンド名</th>
              <th>保有口数</th>
              <th>取得単価</th>
              <th>基準価額</th>
              <th>取得金額</th>
              <th>評価額</th>
              <th>評価損益</th>
              <th>損益率</th>
              <th>分配金</th>
            </tr>
          </thead>
          <tbody>
            {cat.funds.map((f) => (
              <tr key={`${cat.category_name}-${f.name}`}>
                <td><span className="name-cell-portfolio">{f.name}</span></td>
                <td className="volume-cell">{f.units}</td>
                <td className="price-cell">{fmtYen(f.cost_price)}</td>
                <td className="price-cell">{fmtYen(f.nav)}</td>
                <td className="volume-cell">{fmtYen(f.cost_total)}</td>
                <td className="price-cell">{fmtYen(f.market_value)}</td>
                <td className={`price-cell ${pnlClass(f.unrealized_pnl)}`}>
                  {fmtPnl(f.unrealized_pnl)}
                </td>
                <td className={`price-cell ${pnlClass(f.unrealized_pnl)}`}>
                  {pnlPct(f.unrealized_pnl, f.cost_total)}
                </td>
                <td className="volume-cell">{f.distribution_method}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function BondCategoryTable({ cat }: { cat: HoldingCategory }) {
  if (!cat.bonds?.length) return null;
  return (
    <div className="portfolio-category">
      <div className="portfolio-category-header">
        <h3>{cat.category_name}</h3>
        <div className="portfolio-category-summary">
          <span className="portfolio-summary-label">評価額</span>
          <span className="portfolio-summary-value">{fmtYen(cat.total_market_value)}</span>
        </div>
      </div>
      <div className="stock-table-container">
        <table className="stock-table">
          <thead>
            <tr>
              <th>銘柄</th>
              <th>利率</th>
              <th>償還日</th>
              <th>利払日</th>
              <th>額面</th>
              <th>取得単価</th>
              <th>評価額</th>
            </tr>
          </thead>
          <tbody>
            {cat.bonds.map((b) => (
              <tr key={b.name}>
                <td><span className="name-cell-portfolio">{b.name}</span></td>
                <td className="price-cell">{b.coupon_rate.toFixed(3)}%</td>
                <td className="volume-cell">{b.maturity_date}</td>
                <td className="volume-cell">{b.coupon_dates}</td>
                <td className="price-cell">{fmtYen(b.face_value)}</td>
                <td className="price-cell">{b.cost_price}</td>
                <td className="price-cell">{fmtYen(b.market_value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getPortfolio()
      .then(setPortfolio)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo" onClick={() => navigate("/")} style={{ cursor: "pointer" }}>K</div>
          <h1>
            Kabu
            <small>智能股票监控平台</small>
          </h1>
        </div>
        <div className="nav-tabs">
          <button className="tab" onClick={() => navigate("/")}>監視一覧</button>
          <button className="tab active">保有証券</button>
        </div>
      </header>

      {loading ? (
        <div className="stock-table-container">
          <div className="loading">
            <div className="spinner" />
            <p>ポートフォリオを読み込み中...</p>
          </div>
        </div>
      ) : !portfolio ? (
        <div className="stock-table-container">
          <div className="empty-state" style={{ padding: 40 }}>
            <h3>データなし</h3>
            <p>ポートフォリオデータが見つかりませんでした</p>
          </div>
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="portfolio-overview">
            <div className="portfolio-stat-card">
              <div className="portfolio-stat-label">総評価額</div>
              <div className="portfolio-stat-value">{fmtYen(portfolio.total_market_value)}</div>
            </div>
            <div className="portfolio-stat-card">
              <div className="portfolio-stat-label">総取得額</div>
              <div className="portfolio-stat-value">{fmtYen(portfolio.total_cost)}</div>
            </div>
            <div className="portfolio-stat-card">
              <div className="portfolio-stat-label">総評価損益</div>
              <div className={`portfolio-stat-value portfolio-stat-pnl ${pnlClass(portfolio.total_pnl)}`}>
                {fmtPnl(portfolio.total_pnl)}
              </div>
            </div>
            <div className="portfolio-stat-card">
              <div className="portfolio-stat-label">損益率</div>
              <div className={`portfolio-stat-value portfolio-stat-pnl ${pnlClass(portfolio.total_pnl)}`}>
                {pnlPct(portfolio.total_pnl, portfolio.total_cost)}
              </div>
            </div>
          </div>

          {/* Category tables */}
          {portfolio.categories.map((cat) => (
            <div key={cat.category_name}>
              {cat.stocks && <StockCategoryTable cat={cat} />}
              {cat.funds && <FundCategoryTable cat={cat} />}
              {cat.bonds && <BondCategoryTable cat={cat} />}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
