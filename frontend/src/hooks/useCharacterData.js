import { useState, useCallback } from 'react';
import * as characterApi from '../api/character';

export const useCharacterData = () => {
    const [searchName, setSearchName] = useState('');
    const [characterData, setCharacterData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = useCallback(async (e) => {
        if (e) e.preventDefault();
        if (!searchName.trim()) return;

        setIsLoading(true);
        setError(null);
        setCharacterData(null);

        try {
            const response = await characterApi.searchCharacter(searchName.trim());
            if (response.data.success) {
                setCharacterData(response.data.data);
            } else {
                setError(response.data.error?.message || '캐릭터를 찾을 수 없습니다.');
            }
        } catch (err) {
            console.error('Search error:', err);
            if (err.response?.data?.error?.message) {
                setError(err.response.data.error.message);
            } else {
                setError('캐릭터 검색 중 오류가 발생했습니다.');
            }
        } finally {
            setIsLoading(false);
        }
    }, [searchName]);

    return {
        searchName,
        setSearchName,
        characterData,
        isLoading,
        error,
        handleSearch
    };
};
