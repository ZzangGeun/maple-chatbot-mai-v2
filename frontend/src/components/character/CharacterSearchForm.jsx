import React from 'react';
import { ArrowRight, Loader2, Search } from 'lucide-react';

const CharacterSearchForm = ({ searchName, setSearchName, handleSearch, isLoading }) => (
    <section className="character-search-panel" aria-label="캐릭터 검색">
        <div className="character-search-heading"><span className="character-search-icon"><Search size={21} aria-hidden="true" /></span><div><h2>모험가를 찾아볼까요?</h2><p>메이플스토리 캐릭터 닉네임을 입력해주세요.</p></div></div>
        <form onSubmit={handleSearch} className="search-input-group">
            <div className="character-search-field">
                <Search size={19} aria-hidden="true" />
                <label className="sr-only" htmlFor="character-nickname">캐릭터 닉네임</label>
                <input id="character-nickname" type="text" className="character-search-input" placeholder="캐릭터 닉네임을 입력하세요" value={searchName} onChange={(e) => setSearchName(e.target.value)} autoComplete="off" required />
            </div>
            <button type="submit" className="character-search-btn" disabled={isLoading || !searchName.trim()}>
                {isLoading ? <Loader2 className="character-loading-icon" size={17} aria-hidden="true" /> : <ArrowRight size={17} aria-hidden="true" />}{isLoading ? '검색 중' : '캐릭터 검색'}
            </button>
        </form>
    </section>
);

export default CharacterSearchForm;
