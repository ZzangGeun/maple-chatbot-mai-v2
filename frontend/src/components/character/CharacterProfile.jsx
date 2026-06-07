import React from 'react';

const CharacterProfile = ({ characterData }) => {
    const basicInfo = characterData?.basic_info;

    return (
        <div className="character-profile-section">
            <div className="profile-card">
                {/* 프로필 이미지 */}
                <div className="profile-image-container">
                    {basicInfo?.character_image ? (
                        <img
                            src={basicInfo.character_image}
                            alt={basicInfo.character_name}
                        />
                    ) : (
                        <div className="profile-image-placeholder">🧙</div>
                    )}
                </div>

                {/* 캐릭터 기본 정보 */}
                <div className="profile-info">
                    <h2 className="profile-character-name">{basicInfo?.character_name}</h2>
                    <div className="profile-class-info">
                        <span className="class-tag">{basicInfo?.character_class}</span>
                        <span className="class-level">{basicInfo?.character_class_level}</span>
                    </div>
                    <div className="profile-detail-row">
                        <span className="detail-label">Lv.{basicInfo?.character_level}</span>
                        <span className="detail-value">{basicInfo?.world_name}</span>
                    </div>
                    <div className="profile-power">
                        <div className="power-label">전투력</div>
                        <div className="power-value">
                            {Number(characterData?.stat_info?.['전투력']).toLocaleString()}
                        </div>
                    </div>

                    {/* 주요 스탯 요약 */}
                    <div className="profile-stats-summary">
                        <div className="summary-stat">
                            <span className="summary-label">길드</span>
                            <span className="summary-value">{basicInfo?.character_guild_name || '없음'}</span>
                        </div>
                        <div className="summary-stat">
                            <span className="summary-label">성별</span>
                            <span className="summary-value">{basicInfo?.character_gender}</span>
                        </div>
                        <div className="summary-stat">
                            <span className="summary-label">인기도</span>
                            <span className="summary-value">{basicInfo?.character_popularity}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CharacterProfile;
