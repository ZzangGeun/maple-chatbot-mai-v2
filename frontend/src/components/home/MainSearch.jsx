import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const MainSearch = () => {
    const [searchText, setSearchText] = useState('');
    const navigate = useNavigate();

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchText.trim()) {
            navigate('/chat', { state: { initialMessage: searchText } });
        }
    };

    const handleExampleClick = (text) => {
        navigate('/chat', { state: { initialMessage: text } });
    };

    return (
        <main className="main-content">
            <h1 className="main-title">메이플 스토리</h1>
            <h2 className="main-subtitle">정보탐색 CHAT BOT</h2>
            <p className="main-description">
                메이플스토리의 모든 정보를 AI와 함께 탐색하세요.<br />
                스킬, 아이템, 사냥터, 보스 공략까지 궁금한 모든 것을 물어보세요!
            </p>

            {/* Main Search Box */}
            <div className="main-search-container">
                <form className="main-search-box" onSubmit={handleSearch}>
                    <input
                        type="text"
                        className="main-search-input"
                        id="mainSearchInput"
                        placeholder="메이플스토리에 관해 무엇이든 물어보세요..."
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                    />
                    <button className="main-search-btn" type="submit">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                        </svg>
                    </button>
                </form>
            </div>

            {/* Search Hint Section */}
            <div className="search-hint">
                <div className="search-hint-title">💡 위 검색창에서 바로 질문해보세요!</div>
                <div className="search-hint-text">질문하면 ChatBot 페이지로 이동하면서 자동으로 질문이 전송됩니다</div>
                <div className="search-examples">
                    {['메르세데스 스킬 알려줘', '180렙 사냥터 추천', '뇌전 드랍 장소', '보스 공략법'].map(text => (
                        <span key={text} className="search-example" onClick={() => handleExampleClick(text)}>{text}</span>
                    ))}
                </div>
            </div>
        </main>
    );
};

export default MainSearch;
