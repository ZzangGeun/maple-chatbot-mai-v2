import React from 'react';

const CharacterRawData = ({ characterData }) => {
    if (!characterData) return null;

    return (
        <div className="info-card">
            <h3 className="info-card-title">🔧 전체 JSON 데이터</h3>
            <pre className="raw-data-pre">
                {JSON.stringify(characterData, null, 2)}
            </pre>
        </div>
    );
};

export default CharacterRawData;
