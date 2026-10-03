import { useState, useCallback, useRef } from 'react';
import * as characterApi from '../api/character';

export const useCharacterSearch = () => {
    const [characterInfo, setCharacterInfo] = useState(null);
    const [charSearchText, setCharSearchText] = useState('');
    const [isCharLoading, setIsCharLoading] = useState(false);
    const [characterTitle, setCharacterTitle] = useState('검색 결과');
    const [characterError, setCharacterError] = useState('');
    const searchTextRef = useRef(charSearchText);
    const requestIdRef = useRef(0);
    searchTextRef.current = charSearchText;

    const handleCharacterSearch = useCallback(async (name, isAuto = false) => {
        const searchName = (name || searchTextRef.current).trim();
        if (!searchName) return;

        const requestId = ++requestIdRef.current;
        setIsCharLoading(true);
        setCharacterError('');
        if (!isAuto) setCharacterTitle('검색 결과');

        try {
            const response = await characterApi.searchCharacter(searchName);
            // 빠르게 다른 캐릭터를 검색하면 가장 최근 요청의 결과만 보여줍니다.
            if (requestId !== requestIdRef.current) return;
            if (response.data.success === true || response.data.status === 'success') {
                setCharacterInfo(response.data.data);
                if (isAuto) setCharacterTitle('내 캐릭터');
            } else {
                setCharacterError(response.data.error?.message
                    || (typeof response.data.error === 'string' ? response.data.error : '')
                    || '캐릭터를 찾을 수 없습니다.');
                setCharacterInfo(null);
            }
        } catch (e) {
            if (requestId !== requestIdRef.current) return;
            setCharacterInfo(null);
            setCharacterError(e.response?.data?.error?.message
                || '캐릭터 정보를 불러오지 못했어요. 잠시 후 다시 검색해주세요.');
        } finally {
            if (requestId === requestIdRef.current) setIsCharLoading(false);
        }
    }, []);

    return {
        characterInfo,
        charSearchText,
        setCharSearchText,
        isCharLoading,
        characterTitle,
        characterError,
        handleCharacterSearch
    };
};
