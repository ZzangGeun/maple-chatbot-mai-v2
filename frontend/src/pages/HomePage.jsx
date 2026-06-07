import React, { useEffect } from 'react';
import Layout from '../components/common/Layout';
import { useAuth } from '../context/AuthContext';
import { useHomeData } from '../hooks/useHomeData';
import { useCharacterSearch } from '../hooks/useCharacterSearch';

import CharacterSidebar from '../components/home/CharacterSidebar';
import MainSearch from '../components/home/MainSearch';
import AdSidebar from '../components/home/AdSidebar';
import NoticeSection from '../components/home/NoticeSection';

import '../styles/pages/home.css';

const HomePage = () => {
    const { user } = useAuth();
    const { homeData, isLoading } = useHomeData();
    const {
        characterInfo,
        charSearchText,
        setCharSearchText,
        isCharLoading,
        characterTitle,
        handleCharacterSearch
    } = useCharacterSearch();

    // Auto-search user's character
    useEffect(() => {
        if (user?.maple_nickname) {
            handleCharacterSearch(user.maple_nickname, true);
        }
    }, [user, handleCharacterSearch]);

    return (
        <Layout>
            <div className="main-container">
                <CharacterSidebar 
                    characterInfo={characterInfo}
                    characterTitle={characterTitle}
                    charSearchText={charSearchText}
                    setCharSearchText={setCharSearchText}
                    isCharLoading={isCharLoading}
                    handleCharacterSearch={handleCharacterSearch}
                />
                <MainSearch />
                <AdSidebar />
            </div>

            {isLoading ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>Loading...</div>
            ) : (
                <NoticeSection 
                    homeData={homeData} 
                    handleCharacterSearch={handleCharacterSearch} 
                />
            )}
        </Layout>
    );
};

export default HomePage;
