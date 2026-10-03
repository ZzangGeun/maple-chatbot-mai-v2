import React from 'react';
import { Bell, Gift, ShoppingBag, Trophy, ArrowUpRight, Inbox, Loader2 as LoaderCircle } from 'lucide-react';

const cards = [
  { key: 'updates', label: '업데이트', caption: '새로운 모험 소식', Icon: Bell, color: 'orange' },
  { key: 'events', label: '이벤트', caption: '놓치기 아까운 즐거움', Icon: Gift, color: 'green' },
  { key: 'cashshop', label: '캐시샵', caption: '오늘의 스타일 체크', Icon: ShoppingBag, color: 'pink' },
];
const formatDate = (item) => {
  const value = item.date || item.date_event_start || item.date_sale_start;
  const date = value && new Date(value);
  return date && !Number.isNaN(date.getTime()) ? date.toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' }) : '';
};
const safeNoticeUrl = (value) => {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : null; } catch { return null; }
};
const NoticeSection = ({ homeData, isLoading, error, handleCharacterSearch }) => {
  const empty = (message) => <div className="notice-empty">{isLoading ? <LoaderCircle className="spin-icon" size={23} aria-hidden="true" /> : <Inbox size={25} strokeWidth={1.5} aria-hidden="true" />}<span>{isLoading ? '소식을 불러오고 있어요' : message}</span></div>;
  return (
    <section className="home-news" aria-labelledby="home-news-title">
      <div className="home-section-intro"><div><span className="section-kicker">MAPLE NOTICE BOARD</span><h2 id="home-news-title">메이플 소식 한눈에</h2></div><span className="section-side-note">모험 전에 가볍게 확인해요</span></div>
      {error && <p className="news-error" role="status">지금은 소식을 불러올 수 없어요. 잠시 후 다시 방문해 주세요.</p>}
      <div className="news-grid">
        {cards.map(({ key, label, caption, Icon, color }) => {
          const items = homeData?.notices?.[key] || [];
          return <section key={key} className="news-card surface-card"><div className="news-card-header"><span className={`news-icon news-icon-${color}`}><Icon size={17} aria-hidden="true" /></span><div><h3>{label}</h3><p>{caption}</p></div></div>
            {items.length ? <div className="notice-list">{items.slice(0, 3).map((item, index) => {
              const href = safeNoticeUrl(item.url);
              const content = <><span>{item.title}</span><small>{formatDate(item)}{href && <ArrowUpRight size={13} aria-hidden="true" />}</small></>;
              return href ? <a key={item.notice_id || index} className="notice-item" href={href} target="_blank" rel="noopener noreferrer">{content}</a> : <div key={item.notice_id || index} className="notice-item">{content}</div>;
            })}</div> : empty(error ? '소식을 잠시 쉬고 있어요' : '아직 등록된 소식이 없어요')}
          </section>;
        })}
        <section className="news-card surface-card"><div className="news-card-header"><span className="news-icon news-icon-yellow"><Trophy size={17} aria-hidden="true" /></span><div><h3>종합 랭킹</h3><p>멋진 모험가들을 만나봐요</p></div></div>
          {homeData?.ranking?.length ? <div className="ranking-list">{homeData.ranking.slice(0, 3).map((rank, index) => <button type="button" className="home-ranking-item" key={rank.character_name || index} onClick={() => handleCharacterSearch(rank.character_name)}><span className="ranking-number">{rank.ranking}</span><span><strong>{rank.character_name}</strong><small>Lv.{rank.character_level}</small></span><ArrowUpRight size={13} aria-hidden="true" /></button>)}</div> : empty(error ? '랭킹을 잠시 쉬고 있어요' : '랭킹을 준비하고 있어요')}
        </section>
      </div>
    </section>
  );
};
export default NoticeSection;
