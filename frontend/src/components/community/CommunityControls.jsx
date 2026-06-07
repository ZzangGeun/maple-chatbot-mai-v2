import React from 'react';
import { getCategoryIcon } from '../../utils/communityUtils';

const CommunityControls = ({
    categories,
    selectedCategory,
    setSelectedCategory,
    searchText,
    setSearchText,
    handleSearch,
    sortBy,
    setSortBy,
    handleWritePost
}) => {
    return (
        <div className="community-controls">
            <div className="category-tabs">
                {categories.map(category => (
                    <button
                        key={category.id}
                        className={`category-tab ${selectedCategory === category.id ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(category.id)}
                    >
                        <span className="category-icon">
                            {category.id === 'all' ? '🌟' : getCategoryIcon(category.id)}
                        </span>
                        <span className="category-name">{category.name}</span>
                        <span className="category-count">({category.count})</span>
                    </button>
                ))}
            </div>

            <div className="community-actions">
                <form className="search-form" onSubmit={handleSearch}>
                    <input
                        type="text"
                        className="search-input"
                        placeholder="제목 or 내용 검색..."
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                    />
                    <button type="submit" className="search-btn">검색</button>
                </form>

                <div className="sort-dropdown">
                    <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="sort-select">
                        <option value="latest">최신순</option>
                        <option value="popular">인기순</option>
                        <option value="views">조회순</option>
                    </select>
                </div>

                <button className="write-btn" onClick={handleWritePost}>
                    ✍️ 글쓰기
                </button>
            </div>
        </div>
    );
};

export default CommunityControls;
