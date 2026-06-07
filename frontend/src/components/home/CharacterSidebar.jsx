import React from 'react';

const CharacterSidebar = ({
    characterInfo,
    characterTitle,
    charSearchText,
    setCharSearchText,
    isCharLoading,
    handleCharacterSearch
}) => {
    const handleSidebarSearchSubmit = (e) => {
        e.preventDefault();
        handleCharacterSearch(charSearchText);
    };

    return (
        <aside className="sidebar-left">
            {/* Character Info Display */}
            <div className="character-info-display" id="characterInfoDisplay">
                <div className="character-info-header">
                    <div className="character-profile-avatar">
                        {characterInfo?.basic_info?.character_image ? (
                            <img src={characterInfo.basic_info.character_image} alt="Character" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                        ) : '🧙‍♂️'}
                    </div>
                    <div className="character-profile-info">
                        <div className="character-profile-name" id="displayCharacterName">
                            {characterInfo ? characterInfo.basic_info.character_name : characterTitle}
                        </div>
                        <div className="character-profile-server" id="displayServerName">
                            {characterInfo ? characterInfo.basic_info.world_name : '-'}
                        </div>
                    </div>
                </div>

                <div className="character-detailed-stats">
                    <div className="detail-stat-row">
                        <span className="detail-stat-label">레벨</span>
                        <span className="detail-stat-value" id="displayCharacterLevel">
                            {characterInfo ? `Lv.${characterInfo.basic_info.character_level}` : '-'}
                        </span>
                    </div>
                    <div className="detail-stat-row">
                        <span className="detail-stat-label">직업</span>
                        <span className="detail-stat-value" id="displayCharacterJob">
                            {characterInfo ? characterInfo.basic_info.character_class : '-'}
                        </span>
                    </div>
                    <div className="detail-stat-row">
                        <span className="detail-stat-label">인기도</span>
                        <span className="detail-stat-value" id="displayCharacterFame">
                            {characterInfo ? characterInfo.basic_info.character_popularity : '-'}
                        </span>
                    </div>
                    {/* 전투력은 stat_info 등에서 추출 필요하지만, 일단 예시로 유지하거나 없으면 - */}
                    <div className="detail-stat-row">
                        <span className="detail-stat-label">길드</span>
                        <span className="detail-stat-value" id="displayCharacterGuild">
                            {characterInfo?.basic_info?.character_guild_name || '-'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Character Search Card */}
            <div className="character-search-card">
                <form className="search-input-group" onSubmit={handleSidebarSearchSubmit}>
                    <input
                        type="text"
                        className="character-search-input"
                        id="characterSearchInput"
                        placeholder="캐릭터 닉네임 입력"
                        value={charSearchText}
                        onChange={(e) => setCharSearchText(e.target.value)}
                    />
                    <button className="character-search-btn" type="submit" disabled={isCharLoading}>
                        <span>{isCharLoading ? '...' : '검색'}</span>
                    </button>
                </form>

                <div className="search-recent" id="recentSearches">
                    <div className="search-recent-title">최근 검색</div>
                    <div className="search-recent-list" id="recentSearchList">
                        {/* 최근 검색어 로직은 추후 구현 가능 */}
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default CharacterSidebar;
