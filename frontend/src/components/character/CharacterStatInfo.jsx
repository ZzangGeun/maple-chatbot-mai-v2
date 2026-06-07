import React from 'react';

const CharacterStatInfo = ({ characterData }) => {
    const statInfo = characterData?.stat_info;
    if (!statInfo) return <div className="info-card"><p>스탯 정보가 없습니다.</p></div>;

    // 주요 스탯 그룹
    const combatStats = [
        { label: '전투력', value: statInfo['전투력'] },
        { label: '최소 스탯공격력', value: statInfo['최소_스탯공격력'] },
        { label: '최대 스탯공격력', value: statInfo['최대_스탯공격력'] },
        { label: '데미지', value: `${statInfo['데미지']}%` },
        { label: '보스 데미지', value: `${statInfo['보스_몬스터_데미지']}%` },
        { label: '최종 데미지', value: `${statInfo['최종_데미지']}%` },
        { label: '방어율 무시', value: `${statInfo['방어율_무시']}%` },
        { label: '크리티컬 확률', value: `${statInfo['크리티컬_확률']}%` },
        { label: '크리티컬 데미지', value: `${statInfo['크리티컬_데미지']}%` },
    ];

    const mainStats = [
        { label: 'STR', value: statInfo['STR'] },
        { label: 'DEX', value: statInfo['DEX'] },
        { label: 'INT', value: statInfo['INT'] },
        { label: 'LUK', value: statInfo['LUK'] },
        { label: 'HP', value: statInfo['HP'] },
        { label: 'MP', value: statInfo['MP'] },
        { label: '공격력', value: statInfo['공격력'] },
        { label: '마력', value: statInfo['마력'] },
    ];

    const forceStats = [
        { label: '스타포스', value: statInfo['스타포스'] },
        { label: '아케인포스', value: statInfo['아케인포스'] },
        { label: '어센틱포스', value: statInfo['어센틱포스'] },
    ];

    const utilityStats = [
        { label: '아이템 드롭률', value: `${statInfo['아이템_드롭률']}%` },
        { label: '메소 획득량', value: `${statInfo['메소_획득량']}%` },
        { label: '버프 지속시간', value: `${statInfo['버프_지속시간']}%` },
        { label: '추가 경험치', value: `${statInfo['추가_경험치_획득']}%` },
    ];

    return (
        <>
            <div className="info-card">
                <h3 className="info-card-title">⚔️ 전투 스탯</h3>
                <div className="stat-grid">
                    {combatStats.map(({ label, value }, idx) => (
                        <div key={idx} className="stat-item">
                            <span className="stat-label">{label}</span>
                            <span className="stat-value" style={{ color: 'var(--primary-color)', fontWeight: '700' }}>
                                {value ?? '-'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="info-card">
                <h3 className="info-card-title">📊 기본 스탯</h3>
                <div className="stat-grid">
                    {mainStats.map(({ label, value }, idx) => (
                        <div key={idx} className="stat-item">
                            <span className="stat-label">{label}</span>
                            <span className="stat-value">{value ?? '-'}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="info-card">
                <h3 className="info-card-title">✨ 포스 / 유틸</h3>
                <div className="stat-grid">
                    {[...forceStats, ...utilityStats].map(({ label, value }, idx) => (
                        <div key={idx} className="stat-item">
                            <span className="stat-label">{label}</span>
                            <span className="stat-value">{value ?? '-'}</span>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
};

export default CharacterStatInfo;
