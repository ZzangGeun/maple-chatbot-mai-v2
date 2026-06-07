import React from 'react';

const CharacterEquipmentInfo = ({ characterData }) => {
    const itemEquipment = characterData?.item_info?.item_equipment;
    if (!itemEquipment) return <div className="info-card"><p>장비 정보가 없습니다.</p></div>;

    const equipmentList = Object.entries(itemEquipment);

    // 잠재 등급 색상
    const getGradeColor = (grade) => {
        if (!grade) return '#999';
        if (grade.includes('레전드리')) return '#00ff00';
        if (grade.includes('유니크')) return '#ffcc00';
        if (grade.includes('에픽')) return '#cc66ff';
        if (grade.includes('레어')) return '#66ccff';
        return '#999';
    };

    return (
        <div className="info-card">
            <h3 className="info-card-title">🎒 장비 정보 ({equipmentList.length}개)</h3>
            <div className="equipment-grid">
                {equipmentList.map(([slot, item], idx) => (
                    <div key={idx} className="equipment-item">
                        <div className="equipment-icon">
                            {item.icon ? (
                                <img src={item.icon} alt={item.name} />
                            ) : (
                                <span style={{ fontSize: '32px' }}>❓</span>
                            )}
                        </div>
                        <div className="equipment-name">{item.name}</div>
                        <div className="equipment-part">{item.part}</div>
                        {item.starforce && item.starforce !== '0' && (
                            <div className="equipment-starforce">⭐ {item.starforce}</div>
                        )}
                        {item.potential_option_grade && (
                            <div
                                className="equipment-potential"
                                style={{
                                    background: `${getGradeColor(item.potential_option_grade)}20`,
                                    color: getGradeColor(item.potential_option_grade),
                                    border: `1px solid ${getGradeColor(item.potential_option_grade)}40`
                                }}
                            >
                                {item.potential_option_grade}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CharacterEquipmentInfo;
