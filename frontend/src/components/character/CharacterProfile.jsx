import React from 'react';
import { Shield, Swords, UserRound } from 'lucide-react';

const CharacterProfile = ({ characterData }) => {
    const basicInfo = characterData?.basic_info;
    const combatPower = characterData?.stat_info?.['전투력'];
    const formattedPower = combatPower != null && Number.isFinite(Number(combatPower)) ? Number(combatPower).toLocaleString('ko-KR') : '-';

    return (
        <aside className="character-profile-section" aria-label="캐릭터 프로필">
            <div className="profile-card">
                <span className="profile-card-heading"><Shield size={14} aria-hidden="true" /> ADVENTURER CARD</span>
                <div className="profile-image-container">
                    <span className="profile-stage-spark" aria-hidden="true">✦</span>
                    {basicInfo?.character_image ? <img src={basicInfo.character_image} alt={`${basicInfo.character_name} 캐릭터`} /> : <UserRound className="profile-image-placeholder" size={64} aria-hidden="true" />}
                    <span className="profile-stage-ground" aria-hidden="true" />
                </div>
                <div className="profile-info">
                    <div className="profile-level">Lv. {basicInfo?.character_level ?? '-'}</div>
                    <h2 className="profile-character-name">{basicInfo?.character_name || '이름 정보 없음'}</h2>
                    <div className="profile-class-info"><span className="class-tag">{basicInfo?.character_class || '-'}</span>{basicInfo?.character_class_level && <span className="class-level">{basicInfo.character_class_level}</span>}</div>
                    <div className="profile-detail-row">{basicInfo?.world_name || '월드 정보 없음'}</div>
                    <div className="profile-power"><div className="power-label"><Swords size={14} aria-hidden="true" /> 전투력</div><div className="power-value">{formattedPower}</div></div>
                    <dl className="profile-stats-summary">
                        <div className="summary-stat"><dt className="summary-label">길드</dt><dd className="summary-value">{basicInfo?.character_guild_name || '없음'}</dd></div>
                        <div className="summary-stat"><dt className="summary-label">성별</dt><dd className="summary-value">{basicInfo?.character_gender || '-'}</dd></div>
                        <div className="summary-stat"><dt className="summary-label">인기도</dt><dd className="summary-value">{basicInfo?.character_popularity ?? '-'}</dd></div>
                    </dl>
                </div>
            </div>
        </aside>
    );
};

export default CharacterProfile;
