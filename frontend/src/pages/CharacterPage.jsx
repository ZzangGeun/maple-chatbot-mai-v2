import React, { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Backpack, BookOpen, AlertCircle as CircleAlert, Compass, FileJson, Loader2, Shield, Sparkles, Swords } from 'lucide-react';
import Layout from '../components/common/Layout';
import { useCharacterData } from '../hooks/useCharacterData';
import CharacterSearchForm from '../components/character/CharacterSearchForm';
import CharacterProfile from '../components/character/CharacterProfile';
import CharacterBasicInfo from '../components/character/CharacterBasicInfo';
import CharacterStatInfo from '../components/character/CharacterStatInfo';
import CharacterEquipmentInfo from '../components/character/CharacterEquipmentInfo';
import CharacterRawData from '../components/character/CharacterRawData';
import '../styles/pages/character.css';

const tabs = [
    { id: 'basic', label: '기본 정보', Icon: BookOpen },
    { id: 'stat', label: '스탯', Icon: Swords },
    { id: 'equipment', label: '장비', Icon: Backpack },
    { id: 'raw', label: '상세 데이터', Icon: FileJson }
];

const CharacterPage = () => {
    const location = useLocation();
    const initialName = typeof location.state?.characterName === 'string' ? location.state.characterName : '';
    const { searchName, setSearchName, characterData, isLoading, error, handleSearch } = useCharacterData(initialName);
    const hasInitialSearch = useRef(false);
    const [activeTab, setActiveTab] = useState('basic');

    useEffect(() => {
        if (initialName && !hasInitialSearch.current) {
            hasInitialSearch.current = true;
            handleSearch();
        }
    }, [initialName, handleSearch]);

    const handleTabKeyDown = (event, index) => {
        let nextIndex;
        if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') nextIndex = (index + tabs.length - 1) % tabs.length;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = tabs.length - 1;
        if (nextIndex !== undefined) {
            event.preventDefault();
            setActiveTab(tabs[nextIndex].id);
            document.getElementById(`character-tab-${tabs[nextIndex].id}`)?.focus();
        }
    };

    return (
        <Layout layoutClass="narrow-layout">
            <div className="character-page-content">
                <header className="character-page-header">
                    <div>
                        <span className="page-eyebrow"><Compass size={15} aria-hidden="true" /> ADVENTURER'S JOURNAL</span>
                        <h1 className="page-heading">모험가 도감<span className="character-heading-star" aria-hidden="true">✦</span></h1>
                        <p className="page-description">내 캐릭터부터 궁금한 모험가까지, 성장의 기록을 만나보세요.</p>
                    </div>
                    <span className="character-header-badge"><Shield size={16} aria-hidden="true" /> 캐릭터 검색</span>
                </header>

                <CharacterSearchForm searchName={searchName} setSearchName={setSearchName} handleSearch={handleSearch} isLoading={isLoading} />

                {error && (
                    <div className="character-error" role="alert">
                        <CircleAlert size={20} aria-hidden="true" />
                        <div><strong>캐릭터를 불러오지 못했어요.</strong><p>{error}</p></div>
                    </div>
                )}

                {isLoading && (
                    <div className="character-loading" role="status" aria-live="polite">
                        <Loader2 className="character-loading-icon" size={32} aria-hidden="true" />
                        <strong>모험가의 기록을 찾고 있어요</strong>
                        <p>캐릭터 정보를 불러오는 중입니다. 잠시만 기다려주세요.</p>
                    </div>
                )}

                {characterData && !isLoading && (
                    <div className="character-main-layout">
                        <CharacterProfile characterData={characterData} />
                        <div className="character-details-section">
                            <div className="character-tabs" role="tablist" aria-label="캐릭터 정보">
                                {tabs.map(({ id, label, Icon }, index) => (
                                    <button key={id} type="button" id={`character-tab-${id}`} role="tab" aria-selected={activeTab === id} aria-controls={`character-panel-${id}`} tabIndex={activeTab === id ? 0 : -1} className={`char-tab-button ${activeTab === id ? 'active' : ''}`} onClick={() => setActiveTab(id)} onKeyDown={(event) => handleTabKeyDown(event, index)}>
                                        <Icon size={16} aria-hidden="true" />{label}
                                    </button>
                                ))}
                            </div>
                            {tabs.map(({ id }) => (
                                <div key={id} className={`char-tab-content ${activeTab === id ? 'active' : ''}`} id={`character-panel-${id}`} role="tabpanel" aria-labelledby={`character-tab-${id}`} hidden={activeTab !== id} tabIndex={0}>
                                    {id === 'basic' && <CharacterBasicInfo characterData={characterData} />}
                                    {id === 'stat' && <CharacterStatInfo characterData={characterData} />}
                                    {id === 'equipment' && <CharacterEquipmentInfo characterData={characterData} />}
                                    {id === 'raw' && <CharacterRawData characterData={characterData} />}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {!characterData && !isLoading && !error && (
                    <section className="character-empty" aria-labelledby="character-empty-title">
                        <div className="character-empty-scene" aria-hidden="true">
                            <span className="scene-spark scene-spark-one">✦</span><span className="scene-spark scene-spark-two">✧</span>
                            <div className="journal-card"><span className="journal-card-label">MY ADVENTURER</span><div className="journal-avatar"><span className="journal-mushroom-cap" /><span className="journal-mushroom-stem"><i /><i /></span></div><span className="journal-card-line" /><span className="journal-card-line short" /></div>
                            <span className="scene-icon scene-icon-sword"><Swords size={25} /></span><span className="scene-icon scene-icon-star"><Sparkles size={24} /></span>
                        </div>
                        <div className="character-empty-copy">
                            <span className="character-empty-kicker">새로운 모험의 첫 페이지</span>
                            <h2 id="character-empty-title">어떤 모험가가 궁금한가요?</h2>
                            <p>닉네임 하나로 캐릭터의 정보와 장비를 한눈에.<br />지금 나만의 모험가 도감을 펼쳐보세요.</p>
                            <div className="character-empty-features">
                                <span><BookOpen size={16} aria-hidden="true" /> 기본 정보</span><span><Swords size={16} aria-hidden="true" /> 전투 스탯</span><span><Backpack size={16} aria-hidden="true" /> 장착 장비</span>
                            </div>
                        </div>
                    </section>
                )}
                <p className="character-data-note">캐릭터 정보는 메이플스토리 공개 데이터를 기준으로 제공됩니다.</p>
            </div>
        </Layout>
    );
};

export default CharacterPage;
