import React from 'react';
import { Link } from 'react-router-dom';
import { Search, UserRound, ArrowUpRight, Loader2 as LoaderCircle, Leaf } from 'lucide-react';

const CharacterSidebar = ({ characterInfo, charSearchText, setCharSearchText, isCharLoading, handleCharacterSearch, characterError }) => {
  const basic = characterInfo?.basic_info;
  return (
    <section className="home-character-card surface-card" aria-labelledby="home-character-title">
      <div className="home-card-heading"><span className="feature-icon feature-icon-green"><UserRound size={20} aria-hidden="true" /></span><div><span className="mini-eyebrow">CHARACTER BOOK</span><h2 id="home-character-title">내 캐릭터를 만나봐요</h2></div></div>
      <div className="home-character-preview">
        <div className={`home-character-avatar${basic?.character_image ? ' has-image' : ''}`}>{basic?.character_image ? <img src={basic.character_image} alt={basic.character_name} /> : <Leaf size={32} strokeWidth={1.5} aria-hidden="true" />}</div>
        <div>{basic ? <><strong>{basic.character_name}</strong><p>{basic.world_name} · Lv.{basic.character_level}</p><span>{basic.character_class}</span></> : <><strong>어떤 모험가인가요?</strong><p>닉네임으로 캐릭터를 찾아보세요.</p></>}</div>
      </div>
      <form className="home-character-form" onSubmit={(e) => { e.preventDefault(); handleCharacterSearch(charSearchText); }}>
        <label htmlFor="home-character-search" className="sr-only">캐릭터 닉네임</label>
        <Search size={16} aria-hidden="true" />
        <input id="home-character-search" placeholder="캐릭터 닉네임 입력" value={charSearchText} onChange={(e) => setCharSearchText(e.target.value)} maxLength={30} />
        <button type="submit" disabled={isCharLoading || !charSearchText.trim()} aria-label="캐릭터 검색">{isCharLoading ? <LoaderCircle className="spin-icon" size={17} aria-hidden="true" /> : <ArrowUpRight size={19} aria-hidden="true" />}</button>
      </form>
      {characterError && <p className="home-inline-error" role="alert">{characterError}</p>}
      <Link to="/character" state={basic ? { characterName: basic.character_name } : undefined} className="home-card-link">스탯과 장비 자세히 보기<ArrowUpRight size={14} aria-hidden="true" /></Link>
    </section>
  );
};
export default CharacterSidebar;
