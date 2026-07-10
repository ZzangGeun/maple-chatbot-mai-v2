import { useState, useEffect } from 'react';
import { createCommunityPost, getCommunityPosts } from '../api/community';

const initialCategories = [
    { id: 'all', name: '전체', count: 0 },
    { id: 'free', name: '자유', count: 0 },
    { id: 'question', name: '질문', count: 0 },
    { id: 'guide', name: '공략', count: 0 },
    { id: 'trade', name: '거래', count: 0 },
    { id: 'guild', name: '길드', count: 0 }
];

/**
 * 커뮤니티 목업 게시글 목록을 카테고리로 필터링하고 정렬 기준으로 정렬한다.
 * 순수 함수(입력을 변형하지 않음)로, 필터·정렬 계약을 테스트 가능하게 노출한다.
 *
 * 계약:
 * - 반환 목록은 항상 원본 `posts`의 부분집합이다(원소 추가 없음).
 * - `category`가 'all'이 아니면 모든 원소의 `category`가 선택값과 일치한다.
 * - `sortBy`에 따라 정렬된다: 'latest'(createdAt 내림차순),
 *   'popular'(likes+comments 내림차순), 'views'(views 내림차순).
 *
 * @param {Array} posts 원본 게시글 배열
 * @param {string} category 선택된 카테고리('all' 포함)
 * @param {string} sortBy 정렬 기준('latest' | 'popular' | 'views')
 * @returns {Array} 필터링·정렬된 새 배열
 */
export const filterAndSortPosts = (posts, category, sortBy) => {
    const filteredPosts = category === 'all'
        ? posts
        : posts.filter(post => post.category === category);

    return [...filteredPosts].sort((a, b) => {
        if (sortBy === 'latest') {
            return new Date(b.createdAt) - new Date(a.createdAt);
        } else if (sortBy === 'popular') {
            return (b.likes + b.comments) - (a.likes + a.comments);
        } else if (sortBy === 'views') {
            return b.views - a.views;
        }
        return 0;
    });
};

export const useCommunity = () => {
    const [posts, setPosts] = useState([]);
    const [categories, setCategories] = useState(initialCategories);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [searchText, setSearchText] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('latest');
    const [isLoading, setIsLoading] = useState(true);
    const [refreshKey, setRefreshKey] = useState(0);
    const [showWriteModal, setShowWriteModal] = useState(false);
    const [writeForm, setWriteForm] = useState({
        title: '',
        content: '',
        category: 'free'
    });

    useEffect(() => {
        let cancelled = false;

        const fetchPosts = async () => {
            setIsLoading(true);
            try {
                const response = await getCommunityPosts({
                    category: selectedCategory,
                    sort: sortBy,
                    search: searchQuery
                });
                if (cancelled) return;

                setPosts(response.data.posts);
                setCategories(current => current.map(category => ({
                    ...category,
                    count: response.data.categoryCounts[category.id] || 0
                })));
            } catch (error) {
                if (!cancelled) console.error('Failed to fetch posts:', error);
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        };

        fetchPosts();
        return () => {
            cancelled = true;
        };
    }, [selectedCategory, sortBy, searchQuery, refreshKey]);

    const handleSubmitPost = async (e) => {
        e.preventDefault();
        try {
            await createCommunityPost(writeForm);
            setShowWriteModal(false);
            setWriteForm({ title: '', content: '', category: 'free' });
            setSelectedCategory('all');
            setSortBy('latest');
            setSearchText('');
            setSearchQuery('');
            setRefreshKey(key => key + 1);
        } catch (error) {
            console.error('Failed to create post:', error);
        }
    };

    const handleSearch = (e) => {
        e.preventDefault();
        setSearchQuery(searchText.trim());
    };

    return {
        posts,
        categories,
        selectedCategory,
        setSelectedCategory,
        searchText,
        setSearchText,
        sortBy,
        setSortBy,
        isLoading,
        showWriteModal,
        setShowWriteModal,
        writeForm,
        setWriteForm,
        handleSubmitPost,
        handleSearch
    };
};
