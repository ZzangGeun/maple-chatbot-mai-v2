import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, MessagesSquare, ArrowUpRight, Compass, Swords, Backpack, Leaf } from 'lucide-react';
import Layout from '../components/common/Layout';
import { useAuth } from '../context/AuthContext';
import { useHomeData } from '../hooks/useHomeData';
import { useCharacterSearch } from '../hooks/useCharacterSearch';
import CharacterSidebar from '../components/home/CharacterSidebar';
import MainSearch from '../components/home/MainSearch';
import NoticeSection from '../components/home/NoticeSection';
import AdSense from '../components/common/AdSense';
import '../styles/pages/home.css';

const guides = [
  { Icon: Compass, title: '레벨에 맞는 사냥터', detail: '다음 목적지를 찾아봐요', question: '내 레벨에 맞는 사냥터를 추천해줘' },
  { Icon: Swords, title: '보스 도전 준비', detail: '공략부터 준비물까지', question: '메이플스토리 보스 도전 순서와 준비를 알려줘' },
  { Icon: Backpack, title: '장비와 성장 가이드', detail: '한 걸음 더 강해지는 방법', question: '메이플스토리 장비를 어떻게 맞추면 좋을까?' },
];
const HomePage = () => {
  const { user } = useAuth();
  const { homeData, isLoading, error } = useHomeData();
  const character = useCharacterSearch();
  const { handleCharacterSearch } = character;
  useEffect(() => {
    if (user?.maple_nickname) handleCharacterSearch(user.maple_nickname, true);
  }, [user?.maple_nickname, handleCharacterSearch]);
  return (
    <Layout>
      <div className="home-page">
        <MainSearch />
        <div className="home-section-intro"><div><span className="section-kicker">READY, SET, ADVENTURE!</span><h2>오늘의 모험, 여기서 시작해요</h2></div><span className="section-side-note"><Leaf size={14} aria-hidden="true" />작은 궁금증부터 큰 도전까지</span></div>
        <div className="home-tools-grid">
          <CharacterSidebar {...character} />
          <section className="home-guide-card surface-card" aria-labelledby="home-guide-title">
            <div className="home-card-heading"><span className="feature-icon feature-icon-orange"><Sparkles size={20} aria-hidden="true" /></span><div><span className="mini-eyebrow">ADVENTURE GUIDE</span><h2 id="home-guide-title">막막할 땐 메이에게</h2></div></div>
            <div className="guide-list">{guides.map(({ Icon, title, detail, question }) => <Link key={title} to="/chat" state={{ initialMessage: question }} className="guide-item"><span className="guide-item-icon"><Icon size={18} aria-hidden="true" /></span><span><strong>{title}</strong><small>{detail}</small></span><ArrowUpRight size={15} aria-hidden="true" /></Link>)}</div>
          </section>
          <section className="home-community-card" aria-labelledby="home-community-title">
            <span className="community-illustration" aria-hidden="true"><MessagesSquare size={43} strokeWidth={1.5} /><span>+</span><Leaf size={19} /></span>
            <span className="mini-eyebrow">TOGETHER IS BETTER</span>
            <h2 id="home-community-title">모험은 함께할 때<br />더 즐거우니까!</h2>
            <p>나만의 꿀팁도, 소소한 일상도.<br />모험가들의 이야기를 만나보세요.</p>
            <Link to="/community" className="community-card-link">커뮤니티 놀러 가기<ArrowUpRight size={17} aria-hidden="true" /></Link>
          </section>
        </div>
        <NoticeSection homeData={homeData} isLoading={isLoading} error={error} handleCharacterSearch={handleCharacterSearch} />
        <AdSense slotName="medium_rectangle" className="home-ad global-ad" />
      </div>
    </Layout>
  );
};
export default HomePage;
