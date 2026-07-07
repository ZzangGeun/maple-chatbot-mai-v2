import client from './client';

export const getHomeData = () => 
  client.get('/api/v1/core/home/data/');

// searchCharacter는 api/character.js가 정본(single source of truth)이다.
// 하위 호환을 위해 재-export한다.
export { searchCharacter } from './character';
