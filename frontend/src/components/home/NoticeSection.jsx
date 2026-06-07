import React from 'react';
import NoticeRoller from './NoticeRoller';
import ImageRoller from './ImageRoller';

const NoticeSection = ({ homeData, handleCharacterSearch }) => {
    return (
        <div className="bottom-section">
            {/* Update Notice Card */}
            <div className="section-card">
                <div className="section-header update-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                    업데이트
                    <div className="nav-arrows">
                        <button className="nav-arrow">◀</button>
                        <button className="nav-arrow">▶</button>
                    </div>
                </div>
                <div className="section-content">
                    <div className="notice-scroll-container" id="updateNoticeContainer">
                        <NoticeRoller notices={homeData.notices.updates} />
                    </div>
                </div>
            </div>

            {/* Event Notice Card */}
            <div className="section-card">
                <div className="section-header event-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                    이벤트
                    <div className="nav-arrows">
                        <button className="nav-arrow">◀</button>
                        <button className="nav-arrow">▶</button>
                    </div>
                </div>
                <div className="section-content">
                    <div className="notice-scroll-container" id="eventNoticeContainer" style={{ overflow: 'hidden' }}>
                        <ImageRoller
                            items={homeData.notices.events}
                            interval={3000}
                            renderItem={(item) => (
                                <div
                                    className="event-display"
                                    onClick={() => item.url && window.open(item.url, '_blank')}
                                    style={{ cursor: 'pointer', padding: item.thumbnail_url ? '0' : '8px', width: '100%', height: '100%', position: 'relative' }}
                                >
                                    {item.thumbnail_url ? (
                                        <>
                                            <img
                                                src={item.thumbnail_url}
                                                alt={item.title}
                                                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' }}
                                            />
                                            <div style={{
                                                position: 'absolute',
                                                bottom: 0,
                                                left: 0,
                                                right: 0,
                                                background: 'rgba(0, 0, 0, 0.6)',
                                                color: 'white',
                                                fontSize: '11px',
                                                padding: '4px 8px',
                                                borderBottomLeftRadius: '8px',
                                                borderBottomRightRadius: '8px',
                                                whiteSpace: 'nowrap',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                textAlign: 'center'
                                            }}>
                                                {item.title}
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <div className="event-icon">🎮</div>
                                            <div className="event-title-modern">{item.title}</div>
                                            <div className="event-date-modern">{item.date_event_start} ~ {item.date_event_end}</div>
                                        </>
                                    )}
                                </div>
                            )}
                        />
                    </div>
                </div>
            </div>

            {/* CashShop Notice Card */}
            <div className="section-card">
                <div className="section-header cash-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                    캐쉬샵
                    <div className="nav-arrows">
                        <button className="nav-arrow">◀</button>
                        <button className="nav-arrow">▶</button>
                    </div>
                </div>
                <div className="section-content">
                    <div className="notice-scroll-container" id="cashshopNoticeContainer" style={{ overflow: 'hidden' }}>
                        <ImageRoller
                            items={homeData.notices.cashshop}
                            interval={4000} // Different interval for variety
                            renderItem={(item) => (
                                <div
                                    className="cash-display"
                                    onClick={() => item.url && window.open(item.url, '_blank')}
                                    style={{ cursor: 'pointer', padding: item.thumbnail_url ? '0' : '8px', width: '100%', height: '100%', position: 'relative' }}
                                >
                                    {item.thumbnail_url ? (
                                        <>
                                            <img
                                                src={item.thumbnail_url}
                                                alt={item.title}
                                                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' }}
                                            />
                                            <div style={{
                                                position: 'absolute',
                                                bottom: 0,
                                                left: 0,
                                                right: 0,
                                                background: 'rgba(0, 0, 0, 0.6)',
                                                color: 'white',
                                                fontSize: '11px',
                                                padding: '4px 8px',
                                                borderBottomLeftRadius: '8px',
                                                borderBottomRightRadius: '8px',
                                                whiteSpace: 'nowrap',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                textAlign: 'center'
                                            }}>
                                                {item.title}
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <div className="cash-banner-image">🎭</div>
                                            <div className="cash-banner-title">{item.title}</div>
                                            <div className="cash-banner-subtitle">판매 종료: {item.date_sale_end || '상시'}</div>
                                        </>
                                    )}
                                </div>
                            )}
                        />
                    </div>
                </div>
            </div>

            {/* Combined Ranking Card */}
            <div className="section-card">
                <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                    종합랭킹
                    <div className="nav-arrows">
                        <button className="nav-arrow">◀</button>
                        <button className="nav-arrow">▶</button>
                    </div>
                </div>
                <div className="section-content">
                    <div className="ranking-scroll-container" id="rankingContainer">
                        {homeData.ranking.map((rank, idx) => (
                            <div
                                className="ranking-item-modern"
                                key={idx}
                                onClick={() => handleCharacterSearch(rank.character_name)}
                                style={{ cursor: 'pointer' }}
                            >
                                <div className={`ranking-badge top-${rank.ranking}`}>{rank.ranking}</div>
                                <div className="ranking-player-info">
                                    <span className="ranking-name">{rank.character_name}</span>
                                    <span className="ranking-details">Lv.{rank.character_level}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NoticeSection;
