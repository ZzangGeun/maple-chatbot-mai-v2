import { useState, useEffect } from 'react';

const mockPostsList = [
    {
        id: 1,
        title: '메르세데스 5차 스킬 공략 공유합니다',
        content: '오늘 메르세데스 5차 스킬 퀘스트를 클리어해서 팁 공유드립니다...',
        category: 'guide',
        author: '메르공략왕',
        authorLevel: 250,
        views: 1250,
        likes: 45,
        comments: 23,
        createdAt: '2024-01-10 15:30',
        isRecommended: true
    },
    {
        id: 2,
        title: '180렙 사냥터 어디가 좋을까요?',
        content: '현재 180레벨 전사인데 사냥터 추천해주세요...',
        category: 'question',
        author: '초보전사',
        authorLevel: 180,
        views: 320,
        likes: 12,
        comments: 18,
        createdAt: '2024-01-10 14:15'
    },
    {
        id: 3,
        title: '레전드리 장비 팝니다',
        content: '캐시 아이템으로 레전드리 장비 정리합니다...',
        category: 'trade',
        author: '장비장수',
        authorLevel: 200,
        views: 890,
        likes: 8,
        comments: 15,
        createdAt: '2024-01-10 13:20'
    },
    {
        id: 4,
        title: '우리 길드원 모집합니다!',
        content: '활동적인 길드에 오실 분을 모집합니다...',
        category: 'guild',
        author: '길드마스터',
        authorLevel: 260,
        views: 450,
        likes: 25,
        comments: 32,
        createdAt: '2024-01-10 12:00'
    },
    {
        id: 5,
        title: '오늘 업데이트 정말 좋네요',
        content: '이번 업데이트로 인해서 게임이 훨씬 재밌어졌어요...',
        category: 'free',
        author: '메이플러버',
        authorLevel: 195,
        views: 670,
        likes: 56,
        comments: 41,
        createdAt: '2024-01-10 11:45',
        isRecommended: true
    }
];

export const useCommunity = (user) => {
    const [posts, setPosts] = useState([]);
    const [mockPosts, setMockPosts] = useState(mockPostsList);
    const [categories, setCategories] = useState([
        { id: 'all', name: '전체', count: 0 },
        { id: 'free', name: '자유', count: 0 },
        { id: 'question', name: '질문', count: 0 },
        { id: 'guide', name: '공략', count: 0 },
        { id: 'trade', name: '거래', count: 0 },
        { id: 'guild', name: '길드', count: 0 }
    ]);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [searchText, setSearchText] = useState('');
    const [sortBy, setSortBy] = useState('latest');
    const [isLoading, setIsLoading] = useState(true);
    const [showWriteModal, setShowWriteModal] = useState(false);
    const [writeForm, setWriteForm] = useState({
        title: '',
        content: '',
        category: 'free'
    });

    useEffect(() => {
        fetchPosts();
    }, [selectedCategory, sortBy, mockPosts]);

    const fetchPosts = async () => {
        setIsLoading(true);
        try {
            const filteredPosts = selectedCategory === 'all'
                ? mockPosts
                : mockPosts.filter(post => post.category === selectedCategory);

            const sortedPosts = [...filteredPosts].sort((a, b) => {
                if (sortBy === 'latest') {
                    return new Date(b.createdAt) - new Date(a.createdAt);
                } else if (sortBy === 'popular') {
                    return (b.likes + b.comments) - (a.likes + a.comments);
                } else if (sortBy === 'views') {
                    return b.views - a.views;
                }
                return 0;
            });

            setPosts(sortedPosts);

            const categoryCounts = categories.map(cat => ({
                ...cat,
                count: cat.id === 'all' ? mockPosts.length : mockPosts.filter(post => post.category === cat.id).length
            }));
            setCategories(categoryCounts);
        } catch (error) {
            console.error('Failed to fetch posts:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmitPost = (e) => {
        e.preventDefault();
        const newPost = {
            id: mockPosts.length + 1,
            title: writeForm.title,
            content: writeForm.content,
            category: writeForm.category,
            author: user?.nickname || user?.username || '익명',
            authorLevel: user?.profile?.level || 100,
            views: 0,
            likes: 0,
            comments: 0,
            createdAt: new Date().toLocaleString('ko-KR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }).replace(/\./g, '-').replace(/:\s*$/, '')
        };

        setMockPosts([newPost, ...mockPosts]);
        setShowWriteModal(false);
        setWriteForm({ title: '', content: '', category: 'free' });
    };

    const handleSearch = (e) => {
        e.preventDefault();
        console.log('Searching for:', searchText);
        // 실제 검색 로직은 백엔드 연동 시 추가
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
