import React from 'react';
import { HeartHandshake, MessagesSquare, Sparkles, Users } from 'lucide-react';
import Layout from '../components/common/Layout';
import { useAuth } from '../context/AuthContext';
import { useCommunity } from '../hooks/useCommunity';
import CommunityControls from '../components/community/CommunityControls';
import CommunityPostList from '../components/community/CommunityPostList';
import CommunityWriteModal from '../components/community/CommunityWriteModal';
import '../styles/pages/community.css';

const CommunityPage = () => {
    const { isLoggedIn, openLoginModal } = useAuth();
    const {
        posts, categories, selectedCategory, setSelectedCategory, searchText, setSearchText,
        sortBy, setSortBy, isLoading, error, submitError, retryPosts, showWriteModal,
        setShowWriteModal, writeForm, setWriteForm, handleSubmitPost, handleSearch
    } = useCommunity();

    const handleWritePost = () => {
        if (!isLoggedIn) { openLoginModal(); return; }
        setShowWriteModal(true);
    };

    return (
        <Layout layoutClass="narrow-layout">
            <div className="community-container">
                <header className="community-header">
                    <div>
                        <span className="page-eyebrow"><MessagesSquare size={15} aria-hidden="true" /> MAPLE COMMUNITY</span>
                        <h1 className="page-heading">모험가들의 이야기</h1>
                        <p className="page-description">작은 질문도, 특별한 순간도. 함께라서 더 즐거운 메이플 라이프.</p>
                    </div>
                    <div className="community-header-art" aria-hidden="true"><span className="community-art-spark">✦</span><div className="community-art-bubble first"><MessagesSquare size={32} /></div><div className="community-art-bubble second"><HeartHandshake size={25} /></div></div>
                </header>
                <div className="community-welcome"><span className="community-welcome-icon"><Users size={19} aria-hidden="true" /></span><div><strong>어서 오세요, 모험가님!</strong><span>오늘의 메이플 이야기를 나눠보세요.</span></div><span className="community-welcome-tag"><Sparkles size={13} aria-hidden="true" /> 함께하는 모험</span></div>
                <CommunityControls categories={categories} selectedCategory={selectedCategory} setSelectedCategory={setSelectedCategory} searchText={searchText} setSearchText={setSearchText} handleSearch={handleSearch} sortBy={sortBy} setSortBy={setSortBy} handleWritePost={handleWritePost} />
                <div className="community-board-layout">
                    <section className="community-board" aria-label="커뮤니티 게시글">
                        <div className="community-board-heading"><h2>{categories.find(category => category.id === selectedCategory)?.name || '전체'} 이야기</h2>{!isLoading && !error && <span>{posts.length.toLocaleString('ko-KR')}개의 게시글</span>}</div>
                        <CommunityPostList posts={posts} isLoading={isLoading} categories={categories} error={error} onRetry={retryPosts} />
                    </section>
                    <aside className="community-sidebar">
                        <section className="community-guide-card"><span className="community-guide-icon"><HeartHandshake size={25} aria-hidden="true" /></span><h2>우리의 작은 약속</h2><p>서로를 존중하는 한마디가<br />따뜻한 커뮤니티를 만들어요.</p><ul><li>질문에는 친절하게 답해주세요.</li><li>좋은 정보는 함께 나눠주세요.</li><li>개인정보는 소중히 지켜주세요.</li></ul><span className="community-guide-footer">오늘도 즐거운 메이플 되세요!</span></section>
                        <div className="community-sidebar-note"><Sparkles size={16} aria-hidden="true" /><p>혼자서는 어려운 모험도<br />함께라면 조금 더 쉬워질 거예요.</p></div>
                    </aside>
                </div>
                {showWriteModal && <CommunityWriteModal setShowWriteModal={setShowWriteModal} writeForm={writeForm} setWriteForm={setWriteForm} handleSubmitPost={handleSubmitPost} categories={categories} submitError={submitError} />}
            </div>
        </Layout>
    );
};

export default CommunityPage;
