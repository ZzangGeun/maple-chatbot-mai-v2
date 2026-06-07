import React from 'react';

const CharacterBasicInfo = ({ characterData }) => {
    const basicInfo = characterData?.basic_info;
    
    if (!basicInfo) return <div className="info-card"><p>기본 정보가 없습니다.</p></div>;

    const fields = [
        { label: '닉네임', value: basicInfo.character_name },
        { label: '레벨', value: basicInfo.character_level },
        { label: '직업', value: basicInfo.character_class },
        { label: '직업 차수', value: basicInfo.character_class_level },
        { label: '월드', value: basicInfo.world_name },
        { label: '성별', value: basicInfo.character_gender },
        { label: '길드', value: basicInfo.character_guild_name || '없음' },
        { label: '인기도', value: basicInfo.character_popularity },
        { label: '경험치 비율', value: `${basicInfo.character_exp_rate}%` },
        { label: '해방 퀘스트', value: basicInfo.liberation_quest_clear === '1' ? '완료' : '미완료' },
        { label: '캐릭터 생성일', value: basicInfo.character_date_create?.split('T')[0] },
    ];

    return (
        <div className="info-card">
            <h3 className="info-card-title">📋 기본 정보</h3>
            <div className="stat-grid">
                {fields.map(({ label, value }, idx) => (
                    <div key={idx} className="stat-item">
                        <span className="stat-label">{label}</span>
                        <span className="stat-value">{value ?? '-'}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CharacterBasicInfo;
