import client from './client';

// 캐릭터 정보 검색
export const searchCharacter = (characterName) =>
    client.get(`/api/character/search/`, { params: { name: characterName } });
