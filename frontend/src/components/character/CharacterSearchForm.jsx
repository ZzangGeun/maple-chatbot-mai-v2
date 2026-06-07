import React from 'react';

const CharacterSearchForm = ({ searchName, setSearchName, handleSearch, isLoading }) => {
    return (
        <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '16px' }}>
                🍁 캐릭터 검색
            </h1>
            <form onSubmit={handleSearch} className="search-input-group">
                <input
                    type="text"
                    className="character-search-input"
                    placeholder="캐릭터 닉네임을 입력하세요"
                    value={searchName}
                    onChange={(e) => setSearchName(e.target.value)}
                />
                <button type="submit" className="character-search-btn" disabled={isLoading}>
                    {isLoading ? '검색 중...' : '🔍 검색'}
                </button>
            </form>
        </div>
    );
};

export default CharacterSearchForm;
