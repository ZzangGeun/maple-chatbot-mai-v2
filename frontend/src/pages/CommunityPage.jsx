import React from 'react';
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
    } = useCommunity();

    const handleWritePost = () => {
        if (!isLoggedIn) {
            openLoginModal();
            return;
        }
        setShowWriteModal(true);
    };

    return (
        <Layout layoutClass="narrow-layout">
            <div className="community-container">
                <div className="community-header">
                    <h1>메이플 커뮤니티</h1>
                    <p>메이플 스토리 플레이어들이 소통하는 공간</p>
                </div>

                <CommunityControls
                    categories={categories}
                    selectedCategory={selectedCategory}
                    setSelectedCategory={setSelectedCategory}
                    searchText={searchText}
                    setSearchText={setSearchText}
                    handleSearch={handleSearch}
                    sortBy={sortBy}
                    setSortBy={setSortBy}
                    handleWritePost={handleWritePost}
                />

                <CommunityPostList 
                    posts={posts} 
                    isLoading={isLoading} 
                    categories={categories} 
                />

                {showWriteModal && (
                    <CommunityWriteModal
                        setShowWriteModal={setShowWriteModal}
                        writeForm={writeForm}
                        setWriteForm={setWriteForm}
                        handleSubmitPost={handleSubmitPost}
                        categories={categories}
                    />
                )}
            </div>
        </Layout>
    );
};

export default CommunityPage;