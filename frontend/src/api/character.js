import client from './client';

// 캐릭터 정보 검색
export const searchCharacter = (characterName) =>
    client.get(`/api/v1/character/search/`, { params: { name: characterName } });
