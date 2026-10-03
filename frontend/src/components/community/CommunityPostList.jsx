import React from 'react';
import { AlertCircle as CircleAlert, Eye, Inbox, Loader2, MessageCircle, RefreshCw, Star, ThumbsUp, UserRound } from 'lucide-react';
import { getCategoryIcon } from '../../utils/communityUtils';

const CommunityPostList = ({ posts, isLoading, categories, error, onRetry }) => (
    <div className="posts-container" aria-busy={isLoading}>
        {isLoading ? (
            <div className="community-state" role="status"><Loader2 size={29} className="community-loading-icon" aria-hidden="true" /><h3>이야기를 불러오고 있어요</h3><p>모험가들의 소식을 잠시만 기다려주세요.</p></div>
        ) : error ? (
            <div className="community-state community-error" role="alert"><span className="community-state-icon"><CircleAlert size={30} aria-hidden="true" /></span><h3>게시글을 불러오지 못했어요</h3><p>{error}</p><button type="button" className="community-retry-btn" onClick={onRetry}><RefreshCw size={15} aria-hidden="true" /> 다시 불러오기</button></div>
        ) : posts.length === 0 ? (
            <div className="community-state"><span className="community-state-icon"><Inbox size={33} aria-hidden="true" /></span><h3>아직 도착한 이야기가 없어요</h3><p>다른 카테고리나 검색어를 살펴보세요.<br />새로운 이야기를 먼저 나눠주셔도 좋아요!</p></div>
        ) : (
            <div className="posts-list">
                {posts.map(post => (
                    <article key={post.id} className="post-item">
                        <div className="post-category"><span className="category-badge" data-category={post.category}><span aria-hidden="true">{getCategoryIcon(post.category)}</span> {categories.find(category => category.id === post.category)?.name || '이야기'}</span>{post.isRecommended && <span className="recommended-badge"><Star size={11} aria-hidden="true" /> 추천</span>}</div>
                        <div className="post-content"><h3 className="post-title">{post.title}</h3><p className="post-preview">{post.content}</p></div>
                        {post.content && <details className="post-details"><summary>이야기 전체 보기<span className="sr-only">: {post.title}</span></summary><p>{post.content}</p></details>}
                        <div className="post-meta">
                            <div className="author-info"><span className="author-avatar"><UserRound size={14} aria-hidden="true" /></span><span className="author-name">{post.author}</span>{post.authorLevel != null && <span className="author-level">Lv. {post.authorLevel}</span>}</div>
                            <div className="post-stats"><span className="post-stat" aria-label={`조회 ${post.views ?? 0}회`}><Eye size={13} aria-hidden="true" />{Number(post.views ?? 0).toLocaleString('ko-KR')}</span><span className="post-stat" aria-label={`추천 ${post.likes ?? 0}개`}><ThumbsUp size={13} aria-hidden="true" />{post.likes ?? 0}</span><span className="post-stat" aria-label={`댓글 ${post.comments ?? 0}개`}><MessageCircle size={13} aria-hidden="true" />{post.comments ?? 0}</span><span className="post-time">{post.createdAt}</span></div>
                        </div>
                    </article>
                ))}
            </div>
        )}
    </div>
);

export default CommunityPostList;
