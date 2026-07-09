import React, { useState } from 'react';
import Layout from '../components/common/Layout';
import { useCharacterData } from '../hooks/useCharacterData';

import CharacterSearchForm from '../components/character/CharacterSearchForm';
import CharacterProfile from '../components/character/CharacterProfile';
import CharacterBasicInfo from '../components/character/CharacterBasicInfo';
import CharacterStatInfo from '../components/character/CharacterStatInfo';
import CharacterEquipmentInfo from '../components/character/CharacterEquipmentInfo';
import CharacterRawData from '../components/character/CharacterRawData';

import '../styles/pages/character.css';
import '../styles/globals/common.css';

const CharacterPage = () => {
    const {
        searchName,
        setSearchName,
        characterData,
        isLoading,
        error,
        handleSearch
    } = useCharacterData();

    const [activeTab, setActiveTab] = useState('basic');

    return (
        <Layout layoutClass="narrow-layout">
            <div className="main-content">
                <CharacterSearchForm 
                    searchName={searchName}
                    setSearchName={setSearchName}
                    handleSearch={handleSearch}
                    isLoading={isLoading}
                />

                {/* 에러 메시지 */}
                {error && (
                    <div style={{
                        padding: '16px',
                        background: 'var(--error-bg)',
                        border: '1px solid var(--error-border)',
                        borderRadius: '12px',
                        color: 'var(--error-text)',
                        marginBottom: '20px'
                    }}>
                        ⚠️ {error}
                    </div>
                )}

                {/* 로딩 상태 */}
                {isLoading && (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px', animation: 'spin 1s linear infinite' }}>🔄</div>
                        캐릭터 정보를 불러오는 중...
                    </div>
                )}

                {/* 캐릭터 정보 */}
                {characterData && !isLoading && (
                    <div className="character-main-layout">
                        {/* 좌측: 캐릭터 프로필 */}
                        <CharacterProfile characterData={characterData} />

                        {/* 우측: 정보 탭 및 콘텐츠 */}
                        <div className="character-details-section">
                            {/* 탭 네비게이션 */}
                            <div className="character-tabs">
                                <button
                                    className={`char-tab-button ${activeTab === 'stat' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('stat')}
                                >
                                    스탯
                                </button>
                                <button
                                    className={`char-tab-button ${activeTab === 'equipment' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('equipment')}
                                >
                                    장비
                                </button>
                                <button
                                    className={`char-tab-button ${activeTab === 'basic' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('basic')}
                                >
                                    정보
                                </button>
                                <button
                                    className={`char-tab-button ${activeTab === 'raw' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('raw')}
                                >
                                    상세
                                </button>
                            </div>

                            {/* 탭 컨텐츠 */}
                            <div className={`char-tab-content ${activeTab === 'stat' ? 'active' : ''}`}>
                                <CharacterStatInfo characterData={characterData} />
                            </div>
                            <div className={`char-tab-content ${activeTab === 'equipment' ? 'active' : ''}`}>
                                <CharacterEquipmentInfo characterData={characterData} />
                            </div>
                            <div className={`char-tab-content ${activeTab === 'basic' ? 'active' : ''}`}>
                                <CharacterBasicInfo characterData={characterData} />
                            </div>
                            <div className={`char-tab-content ${activeTab === 'raw' ? 'active' : ''}`}>
                                <CharacterRawData characterData={characterData} />
                            </div>
                        </div>
                    </div>
                )}

                {/* 검색 전 안내 */}
                {!characterData && !isLoading && !error && (
                    <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: '64px', marginBottom: '20px' }}>🍁</div>
                        <h2 style={{ fontSize: '22px', fontWeight: '600', marginBottom: '12px', color: 'var(--text-secondary)' }}>
                            캐릭터를 검색해보세요
                        </h2>
                        <p>메이플스토리 캐릭터 닉네임을 입력하면 상세 정보를 확인할 수 있습니다.</p>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default CharacterPage;
