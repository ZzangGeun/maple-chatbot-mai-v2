import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Sparkles, Send, Swords, Compass, Lightbulb, Leaf } from 'lucide-react';
import AdventureScene from './AdventureScene';

const examples = ['처음 시작하는데 어떤 직업이 좋을까?', '200레벨 이후 사냥터 추천해줘', '보스 공략 준비를 도와줘'];
const MainSearch = () => {
  const [searchText, setSearchText] = useState('');
  const navigate = useNavigate();
  const ask = (text) => navigate('/chat', { state: { initialMessage: text.trim() } });
  const handleSearch = (event) => {
    event.preventDefault();
    if (searchText.trim()) ask(searchText);
  };
  return (
    <section className="home-hero" aria-labelledby="hero-title">
      <div className="hero-copy">
        <div className="hero-badge"><span className="badge-dot" />당신의 메이플 모험 파트너<Leaf size={13} aria-hidden="true" /></div>
        <h1 id="hero-title">오늘의 모험도,<br /><span>메이와 함께!</span><Sparkles className="hero-title-sparkle" size={29} aria-hidden="true" /></h1>
        <p className="hero-description">어디서 사냥할까? 어떤 장비가 좋을까?<br />메이플의 크고 작은 궁금증, 메이가 함께 풀어줄게요.</p>
        <form className="hero-question-form" onSubmit={handleSearch}>
          <Sparkles size={21} className="hero-input-icon" aria-hidden="true" />
          <input aria-label="메이에게 물어볼 질문" placeholder="모험 중 궁금한 건 무엇인가요?" value={searchText} onChange={(e) => setSearchText(e.target.value)} maxLength={2000} />
          <button type="submit" aria-label="메이에게 질문하기" disabled={!searchText.trim()}><Send size={19} aria-hidden="true" /></button>
        </form>
        <div className="hero-examples">
          <span className="hero-examples-label"><Lightbulb size={13} aria-hidden="true" />이렇게 물어봐요</span>
          <div>{examples.map((text, index) => (
            <button type="button" key={text} onClick={() => ask(text)}>{index === 0 ? '직업 추천' : index === 1 ? '사냥터 찾기' : '보스 공략'}<ArrowUpRight size={12} aria-hidden="true" /></button>
          ))}</div>
        </div>
      </div>
      <div className="hero-world">
        <span className="world-label"><Compass size={13} aria-hidden="true" />MAPLE ADVENTURE</span>
        <div className="world-speech">반가워요, 모험가님!<span>오늘은 어디로 떠나볼까요?</span></div>
        <AdventureScene />
        <div className="world-tag world-tag-level"><Sparkles size={15} aria-hidden="true" /><div><small>YOUR COMPANION</small><strong>메이 · MAI</strong></div><span className="companion-dot" /></div>
        <div className="world-tag world-tag-quest"><Swords size={15} aria-hidden="true" /><span>함께라면 모험 준비 완료!</span></div>
        <span className="world-coordinate">새로운 모험이 시작되는 곳</span>
      </div>
    </section>
  );
};
export default MainSearch;
