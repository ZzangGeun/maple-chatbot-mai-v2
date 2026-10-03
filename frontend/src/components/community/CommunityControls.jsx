import React from 'react';
import { BookOpen, HelpCircle as CircleHelp, Coins, LayoutGrid, MessageCircle, PencilLine, Search, Shield } from 'lucide-react';

const categoryIcons = { all: LayoutGrid, free: MessageCircle, question: CircleHelp, guide: BookOpen, trade: Coins, guild: Shield };

const CommunityControls = ({ categories, selectedCategory, setSelectedCategory, searchText, setSearchText, handleSearch, sortBy, setSortBy, handleWritePost }) => (
    <div className="community-controls">
        <div className="category-tabs" aria-label="게시글 카테고리">
            {categories.map(category => {
                const Icon = categoryIcons[category.id] || MessageCircle;
                return (
                    <button key={category.id} type="button" className={`category-tab ${selectedCategory === category.id ? 'active' : ''}`} aria-pressed={selectedCategory === category.id} onClick={() => setSelectedCategory(category.id)}>
                        <Icon size={16} aria-hidden="true" /><span className="category-name">{category.name}</span><span className="category-count">{category.count}</span>
                    </button>
                );
            })}
        </div>
        <div className="community-actions">
            <form className="community-search-form" onSubmit={handleSearch}>
                <Search size={17} aria-hidden="true" />
                <label className="sr-only" htmlFor="community-search">게시글 제목 또는 내용 검색</label>
                <input id="community-search" type="search" className="community-search-input" placeholder="궁금한 이야기를 찾아보세요" value={searchText} onChange={(event) => setSearchText(event.target.value)} />
                <button type="submit" className="community-search-btn">검색</button>
            </form>
            <div className="community-action-buttons">
                <label className="sr-only" htmlFor="community-sort">게시글 정렬</label>
                <select id="community-sort" value={sortBy} onChange={(event) => setSortBy(event.target.value)} className="community-sort-select"><option value="latest">최신순</option><option value="popular">인기순</option><option value="views">조회순</option></select>
                <button type="button" className="community-write-btn" onClick={handleWritePost}><PencilLine size={16} aria-hidden="true" /> 이야기 쓰기</button>
            </div>
        </div>
    </div>
);

export default CommunityControls;
