// Import required functions from common module
import { changeEvent, changeCashItem } from './modules/carousel.js';
import { setActiveNavItem } from './common.js';

// DOM이 완전히 로드된 후 스크립트 실행
document.addEventListener('DOMContentLoaded', function() {

    // ===================================================================
    // 함수 정의
    // ===================================================================

    /**
     * 공지사항 데이터를 기반으로 공지 목록을 캐러셀 형태로 렌더링합니다.
     * @param {string} containerSelector - 공지 목록을 담을 컨테이너의 CSS 선택자
     * @param {Array} noticeData - 공지사항 데이터 배열
     */
    function populateNotice(containerSelector, noticeData) {
        const container = document.querySelector(containerSelector);
        if (!container) return;
        
        if (!noticeData || noticeData.length === 0) {
            container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; padding: 8px; text-align: center;"><div style="font-size: 12px; color: var(--text-muted);">공지사항이 없습니다.</div></div>';
            return;
        }

        container.innerHTML = ''; // 기존 내용 비우기
        
        // 데이터를 컨테이너에 저장 (캐러셀 네비게이션용)
        container.dataset.noticeData = JSON.stringify(noticeData);
        container.dataset.currentIndex = '0';
        container.dataset.totalItems = noticeData.length;
        
        let currentIndex = 0;
        const carouselDiv = document.createElement('div');
        carouselDiv.className = 'notice-carousel';
        carouselDiv.style.transition = 'opacity 0.3s ease';
        
        // 현재 아이템을 표시하는 함수
        function showNotice(index) {
            const item = noticeData[index];
            carouselDiv.innerHTML = `
                <div class="notice-carousel-item">
                    <div class="notice-carousel-title">${item.title || '제목 없음'}</div>
                    ${item.url ? `<a href="${item.url}" target="_blank" class="notice-carousel-link">자세히 보기 →</a>` : ''}
                    <div class="carousel-counter">${index + 1} / ${noticeData.length}</div>
                </div>
            `;
        }
        
        container.appendChild(carouselDiv);
        
        // 초기 공지 표시
        showNotice(0);
        
        // 캐러셀 자동 회전 (5초마다)
        const carouselInterval = setInterval(() => {
            currentIndex = (currentIndex + 1) % noticeData.length;
            showNotice(currentIndex);
            container.dataset.currentIndex = currentIndex;
        }, 5000);
        
        // 컨테이너에 인터벌 정보 저장 (필요시 정리용)
        container.dataset.carouselInterval = carouselInterval;
    }

    /**
     * JSON API에서 공지사항 데이터를 비동기로 로드합니다.
     */
    async function loadNoticeFromJSON() {
        try {
            const response = await fetch('/api/notices/json/');
            const result = await response.json();
            
            if (result.status === 'success' && result.data) {
                const data = result.data;
                
                // Helper 함수: 리스트 추출
                function extractList(data) {
                    if (Array.isArray(data)) return data;
                    if (typeof data === 'object' && data !== null) {
                        for (let key of ['event_notice', 'update_notice', 'cashshop_notice', 'notices', 'data', 'results']) {
                            if (Array.isArray(data[key])) return data[key];
                        }
                    }
                    return [];
                }
                
                const updates = extractList(data.notice_update);
                const events = extractList(data.notice_event);
                const cashshops = extractList(data.notice_cashshop);
                
                // 공지사항 렌더링
                populateNotice('#updateNoticeContainer', updates);
                populateNotice('#eventNoticeContainer', events);
                populateNotice('#cashshopNoticeContainer', cashshops);
                
                console.log('JSON API에서 공지사항 데이터 로드 완료', { updates, events, cashshops });
            }
        } catch (error) {
            console.error('JSON API 로드 중 오류 발생:', error);
        }
    }

    /**
     * 공지사항 캐러셀을 조작합니다.
     * @param {string} containerId - 컨테이너 ID (updateNoticeContainer, eventNoticeContainer, cashshopNoticeContainer)
     * @param {number} direction - 방향 (-1: 이전, 1: 다음)
     */
    function changeNoticeCarousel(containerId, direction) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const carousel = container.querySelector('.notice-carousel');
        if (!carousel) return;
        
        // 데이터 상태 가져오기 (컨테이너에 저장된 데이터)
        let currentIndex = parseInt(container.dataset.currentIndex || '0');
        const totalItems = parseInt(container.dataset.totalItems || '1');
        
        // 인덱스 업데이트
        currentIndex += direction;
        if (currentIndex < 0) currentIndex = totalItems - 1;
        if (currentIndex >= totalItems) currentIndex = 0;
        
        container.dataset.currentIndex = currentIndex;
        
        // 페이드 아웃 후 콘텐츠 변경
        carousel.style.opacity = '0';
        setTimeout(() => {
            // 데이터 가져오기 (container에 저장된 noticeData)
            const noticeData = JSON.parse(container.dataset.noticeData || '[]');
            if (noticeData.length === 0) return;
            
            const item = noticeData[currentIndex];
            carousel.innerHTML = `
                <div class="notice-carousel-item">
                    <div class="notice-carousel-title">${item.title || '제목 없음'}</div>
                    ${item.url ? `<a href="${item.url}" target="_blank" class="notice-carousel-link">자세히 보기 →</a>` : ''}
                    <div class="carousel-counter">${currentIndex + 1} / ${noticeData.length}</div>
                </div>
            `;
            carousel.style.opacity = '1';
        }, 150);
    }

    /**
     * 랭킹 데이터를 기반으로 랭킹 목록을 캐러셀 형태로 렌더링합니다.
     * @param {string} containerSelector - 랭킹 목록을 담을 컨테이너의 CSS 선택자
     * @param {Array} rankingData - 랭킹 그룹 배열 (각 그룹은 5명씩) 또는 단일 항목 배열
     */
    function populateRanking(containerSelector, rankingData) {
        const container = document.querySelector(containerSelector);
        if (!container) return;
        
        if (!rankingData || rankingData.length === 0) {
            container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; padding: 8px; text-align: center;"><div style="font-size: 12px; color: var(--text-muted);">랭킹 데이터가 없습니다.</div></div>';
            return;
        }

        // 안정성: 입력이 (a) 단일 항목 리스트, (b) 그룹화된 리스트,
        // 또는 (c) 혼합된 중첩 리스트일 수 있으므로 먼저 플래튼(flatten)합니다.
        const flatList = [];
        rankingData.forEach(item => {
            if (Array.isArray(item)) {
                item.forEach(inner => {
                    if (inner) flatList.push(inner);
                });
            } else if (item) {
                flatList.push(item);
            }
        });

        // 이제 항상 5개씩 정확히 그룹화해서 사용
        const groupedData = [];
        for (let i = 0; i < flatList.length; i += 5) {
            groupedData.push(flatList.slice(i, i + 5));
        }

        container.innerHTML = ''; // 기존 내용 비우기
        
        // 데이터를 컨테이너에 저장 (캐러셀 네비게이션용)
        container.dataset.rankingData = JSON.stringify(groupedData);
        container.dataset.currentIndex = '0';
        container.dataset.totalItems = groupedData.length;
        
        let currentIndex = 0;
        const carouselDiv = document.createElement('div');
        carouselDiv.className = 'ranking-carousel';
        carouselDiv.style.transition = 'opacity 0.3s ease';
        
        // 현재 그룹을 표시하는 함수
        function showRankingGroup(index) {
            const group = groupedData[index];
            
            if (!group || !Array.isArray(group)) {
                console.error(`Group at index ${index} is not valid:`, group);
                return;
            }
            
            let html = '<div class="ranking-carousel-item">';
            
            // 그룹 내 5명의 랭킹 표시
            group.forEach((item, idx) => {
                if (!item) {
                    console.warn(`Item at ${idx} is null/undefined`);
                    return;
                }
                
                const rankBadgeClass = item.ranking <= 5 ? `top-${item.ranking}` : 'other';
                html += `
                    <div class="ranking-group-item" style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #eee;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="ranking-badge ${rankBadgeClass}" style="min-width: 30px; text-align: center;">${item.ranking}</div>
                            <div style="flex: 1;">
                                <div class="ranking-carousel-name" style="margin: 0;">${item.character_name}</div>
                                <div class="ranking-carousel-level" style="margin: 2px 0;">Lv.${item.character_level}</div>
                                <div class="ranking-carousel-world" style="margin: 0;">${item.world_name}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            const startRank = group[0]?.ranking || '?';
            const endRank = group[group.length - 1]?.ranking || '?';
            html += `<div class="carousel-counter" style="text-align: center; margin-top: 8px;">${startRank}~${endRank} / Top 50</div>`;
            html += '</div>';
            
            carouselDiv.innerHTML = html;
        }
        
        container.appendChild(carouselDiv);
        
        // 초기 랭킹 그룹 표시
        showRankingGroup(0);
        
        // 캐러셀 자동 회전 (5초마다)
        const carouselInterval = setInterval(() => {
            currentIndex = (currentIndex + 1) % groupedData.length;
            showRankingGroup(currentIndex);
            container.dataset.currentIndex = currentIndex;
        }, 5000);
        
        // 컨테이너에 인터벌 정보 저장 (필요시 정리용)
        container.dataset.carouselInterval = carouselInterval;
    }

    /**
     * 랭킹 캐러셀을 조작합니다.
     * @param {string} containerId - 컨테이너 ID (rankingContainer)
     * @param {number} direction - 방향 (-1: 이전, 1: 다음)
     */
    function changeRankingCarousel(containerId, direction) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const carousel = container.querySelector('.ranking-carousel');
        if (!carousel) return;
        
        // 데이터 상태 가져오기
        let currentIndex = parseInt(container.dataset.currentIndex || '0');
        const totalItems = parseInt(container.dataset.totalItems || '1');
        
        // 인덱스 업데이트
        currentIndex += direction;
        if (currentIndex < 0) currentIndex = totalItems - 1;
        if (currentIndex >= totalItems) currentIndex = 0;
        
        container.dataset.currentIndex = currentIndex;
        
        // 페이드 아웃 후 콘텐츠 변경
        carousel.style.opacity = '0';
        setTimeout(() => {
            // 데이터 가져오기
            const rankingData = JSON.parse(container.dataset.rankingData || '[]');
            if (rankingData.length === 0) {
                console.error('No ranking data available');
                carousel.style.opacity = '1';
                return;
            }
            
            const group = rankingData[currentIndex];
            
            if (!group || !Array.isArray(group)) {
                console.error(`Group at index ${currentIndex} is not valid:`, group);
                carousel.style.opacity = '1';
                return;
            }
            
            let html = '<div class="ranking-carousel-item">';
            
            // 그룹 내 항목 표시
            group.forEach((item, idx) => {
                if (!item) {
                    console.warn(`Item at ${idx} is null/undefined`);
                    return;
                }
                
                const rankBadgeClass = item.ranking <= 3 ? `top-${item.ranking}` : 'other';
                html += `
                    <div class="ranking-group-item" style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #eee;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="ranking-badge ${rankBadgeClass}" style="min-width: 30px; text-align: center;">${item.ranking}</div>
                            <div style="flex: 1;">
                                <div class="ranking-carousel-name" style="margin: 0;">${item.character_name}</div>
                                <div class="ranking-carousel-level" style="margin: 2px 0;">Lv.${item.character_level}</div>
                                <div class="ranking-carousel-world" style="margin: 0;">${item.world_name}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            const startRank = group[0]?.ranking || '?';
            const endRank = group[group.length - 1]?.ranking || '?';
            html += `<div class="carousel-counter" style="text-align: center; margin-top: 8px;">${startRank}~${endRank} / Top 50</div>`;
            html += '</div>';
            
            carousel.innerHTML = html;
            carousel.style.opacity = '1';
        }, 150);
    }

    // 검색 예시 클릭 시 메인 검색창에 텍스트를 설정하고 검색을 실행합니다.
    function searchExample(query) {
        const mainSearchInput = document.getElementById('mainSearchInput');
        if (mainSearchInput) {
            mainSearchInput.value = query;
            // performMainSearch 함수가 전역에 정의되어 있다고 가정
            if (window.performMainSearch) {
                window.performMainSearch();
            } else {
                // Fallback: chatbot 페이지로 쿼리와 함께 이동
                sessionStorage.setItem('pendingChatQuery', query);
                window.location.href = '/chatbot/';
            }
        }
    }

    // ===================================================================
    // 이벤트 리스너 바인딩
    // ===================================================================

    // 메인 챗봇 검색
    document.querySelector('.main-search-btn')?.addEventListener('click', () => {
        // performMainSearch 함수는 common.js에 있다고 가정
        if (window.performMainSearch) performMainSearch();
    });

    // 검색 예시
    document.querySelectorAll('.search-example').forEach(item => {
        item.addEventListener('click', () => {
            searchExample(item.textContent);
        });
    });

    // 하단 섹션 카드 네비게이션
    // 하단 섹션 카드 네비게이션 (더 견고한 선택자 접근: nav-arrows 내부의 .nav-arrow들 사용)
    const eventCard = document.querySelector('.bottom-section .section-card:nth-child(1)');
    const eventArrows = eventCard?.querySelectorAll('.nav-arrow');
    if (eventArrows?.[0]) eventArrows[0].addEventListener('click', () => changeNoticeCarousel('updateNoticeContainer', -1));
    if (eventArrows?.[1]) eventArrows[1].addEventListener('click', () => changeNoticeCarousel('updateNoticeContainer', 1));

    const eventCard2 = document.querySelector('.bottom-section .section-card:nth-child(2)');
    const eventArrows2 = eventCard2?.querySelectorAll('.nav-arrow');
    if (eventArrows2?.[0]) eventArrows2[0].addEventListener('click', () => changeNoticeCarousel('eventNoticeContainer', -1));
    if (eventArrows2?.[1]) eventArrows2[1].addEventListener('click', () => changeNoticeCarousel('eventNoticeContainer', 1));

    const cashCard = document.querySelector('.bottom-section .section-card:nth-child(3)');
    const cashArrows = cashCard?.querySelectorAll('.nav-arrow');
    if (cashArrows?.[0]) cashArrows[0].addEventListener('click', () => changeNoticeCarousel('cashshopNoticeContainer', -1));
    if (cashArrows?.[1]) cashArrows[1].addEventListener('click', () => changeNoticeCarousel('cashshopNoticeContainer', 1));

    const rankingCard = document.querySelector('.bottom-section .section-card:nth-child(4)');
    const rankingArrows = rankingCard?.querySelectorAll('.nav-arrow');
    if (rankingArrows?.[0]) rankingArrows[0].addEventListener('click', () => changeRankingCarousel('rankingContainer', -1));
    if (rankingArrows?.[1]) rankingArrows[1].addEventListener('click', () => changeRankingCarousel('rankingContainer', 1));

    // ===================================================================
    // 초기화 코드
    // ===================================================================

    setActiveNavItem('홈');

    // 공지사항 데이터 로드: 
    // 1. 먼저 서버에서 주입된 데이터 사용 (빠른 로딩)
    // 2. 없으면 JSON API에서 비동기 로드 (업데이트된 데이터)
    if (window.noticeBackendData) {
        populateNotice('#updateNoticeContainer', window.noticeBackendData.updates);
        populateNotice('#eventNoticeContainer', window.noticeBackendData.events);
        populateNotice('#cashshopNoticeContainer', window.noticeBackendData.cashshops);
        console.log('서버 주입 데이터에서 공지사항 로드 완료');
    } else {
        // Fallback: JSON API에서 로드
        loadNoticeFromJSON();
    }

    // 랭킹 데이터 로드
    if (window.rankingBackendData && window.rankingBackendData.ranking) {
        console.log('Ranking backend data:', window.rankingBackendData.ranking);
        console.log('Ranking data type:', typeof window.rankingBackendData.ranking);
        console.log('Is array:', Array.isArray(window.rankingBackendData.ranking));
        console.log('First item:', window.rankingBackendData.ranking[0]);
        
        populateRanking('#rankingContainer', window.rankingBackendData.ranking);
        console.log('서버 주입 데이터에서 랭킹 로드 완료');
    } else {
        console.log('Ranking backend data missing:', window.rankingBackendData);
    }

    // 캐러셀은 common.js의 initializeCommon에서 이미 초기화됨

});