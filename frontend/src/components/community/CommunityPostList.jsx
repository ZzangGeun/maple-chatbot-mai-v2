import React from 'react';
import { getCategoryIcon } from '../../utils/communityUtils';

const CommunityPostList = ({ posts, isLoading, categories }) => {
    return (
        <div className="posts-container">
            {isLoading ? (
                <div className="loading">로딩 중...</div>
            ) : posts.length === 0 ? (
                <div className="empty-posts">
                    <div className="empty-icon">📭</div>
                    <p>아직 게시글이 없습니다.</p>
                    <p>첫 번째 게시글을 작성해보세요!</p>
                </div>
            ) : (
                <div className="posts-list">
                    {posts.map(post => (
                        <div key={post.id} className="post-item">
                            <div className="post-category">
                                <span className="category-badge" data-category={post.category}>
                                    {getCategoryIcon(post.category)} {categories.find(c => c.id === post.category)?.name}
                                </span>
                                {post.isRecommended && <span className="recommended-badge">⭐ 추천</span>}
                            </div>

                            <div className="post-content">
                                <h3 className="post-title">{post.title}</h3>
                                <p className="post-preview">{post.content}</p>
                            </div>

                            <div className="post-meta">
                                <div className="author-info">
                                    <span className="author-name">{post.author}</span>
                                    <span className="author-level">Lv.{post.authorLevel}</span>
                                </div>

                                <div className="post-stats">
                                    <span className="stat">👁️ {post.views.toLocaleString()}</span>
                                    <span className="stat">👍 {post.likes}</span>
                                    <span className="stat">💬 {post.comments}</span>
                                    <span className="post-time">{post.createdAt}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default CommunityPostList;
