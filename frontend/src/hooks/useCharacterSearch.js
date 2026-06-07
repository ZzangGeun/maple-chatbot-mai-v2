import { useState, useCallback } from 'react';
import * as homeApi from '../api/home';

export const useCharacterSearch = () => {
    const [characterInfo, setCharacterInfo] = useState(null);
    const [charSearchText, setCharSearchText] = useState('');
    const [isCharLoading, setIsCharLoading] = useState(false);
    const [characterTitle, setCharacterTitle] = useState('검색 결과');

    const handleCharacterSearch = useCallback(async (name, isAuto = false) => {
        const searchName = name || charSearchText;
        if (!searchName || !searchName.trim()) return;

        setIsCharLoading(true);
        if (!isAuto) setCharacterTitle('검색 결과');

        try {
            const response = await homeApi.searchCharacter(searchName);
            if (response.data.status === 'success') {
                setCharacterInfo(response.data.data);
                if (isAuto) setCharacterTitle('내 캐릭터');
            } else {
                if (!isAuto) alert(response.data.error || '캐릭터를 찾을 수 없습니다.');
                setCharacterInfo(null);
            }
        } catch (e) {
            console.error(e);
            if (!isAuto) alert('캐릭터 검색 중 오류가 발생했습니다.');
        } finally {
            setIsCharLoading(false);
        }
    }, [charSearchText]);

    return {
        characterInfo,
        charSearchText,
        setCharSearchText,
        isCharLoading,
        characterTitle,
        handleCharacterSearch
    };
};
