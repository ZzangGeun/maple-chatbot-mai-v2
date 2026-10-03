import React from 'react';
import { Backpack, Package, Star } from 'lucide-react';

const CharacterEquipmentInfo = ({ characterData }) => {
    const itemEquipment = characterData?.item_info?.item_equipment;
    if (!itemEquipment) return <div className="info-card"><p>장비 정보가 없습니다.</p></div>;

    const equipmentList = Object.entries(itemEquipment);

    // 잠재 등급 색상
    const getGradeColor = (grade) => {
        if (!grade) return '#75826a';
        if (grade.includes('레전드리')) return '#4d823a';
        if (grade.includes('유니크')) return '#a67925';
        if (grade.includes('에픽')) return '#9560a8';
        if (grade.includes('레어')) return '#4e86a7';
        return '#75826a';
    };

    return (
        <div className="info-card">
            <h3 className="info-card-title"><Backpack size={18} aria-hidden="true" /> 장착 장비 <span>· {equipmentList.length}개</span></h3>
            <div className="equipment-grid">
                {equipmentList.map(([slot, item], idx) => (
                    <div key={idx} className="equipment-item">
                        <div className="equipment-icon">
                            {item.icon ? (
                                <img src={item.icon} alt={item.name} />
                            ) : (
                                <Package size={27} aria-hidden="true" />
                            )}
                        </div>
                        <div className="equipment-name">{item.name}</div>
                        <div className="equipment-part">{item.part}</div>
                        {item.starforce && item.starforce !== '0' && (
                            <div className="equipment-starforce"><Star size={12} aria-hidden="true" /> {item.starforce}</div>
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
