import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

const RollerContainer = styled.div`
  height: 100%;
  overflow: hidden;
  position: relative;
`;

const RollerList = styled.div`
  transition: transform 0.5s ease-in-out;
  transform: translateY(-${props => props.$index * 36}px); /* 높이는 item 높이에 맞춤 */
`;

const NoticeItem = styled.div`
  height: 36px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 13px;
  color: var(--text-dark);
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;

  &:hover {
    background-color: var(--background-hover);
    color: var(--link-pink);
  }
`;

const NoticeRoller = ({ notices }) => {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!notices || notices.length <= 1) return;

    const interval = setInterval(() => {
      setIndex(prev => (prev + 1) % notices.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [notices]);

  if (!notices || notices.length === 0) {
    return <div style={{ padding: '10px', color: 'var(--text-placeholder)', fontSize: '12px', textAlign: 'center' }}>등록된 공지가 없습니다.</div>;
  }

  return (
    <RollerContainer>
      {/* 무한 롤링처럼 보이게 하려면 리스트를 복제해야 하지만, 간단하게 순환으로 구현 */}
      <RollerList $index={index}>
        {notices.map((notice, idx) => (
          <NoticeItem key={idx} onClick={() => window.open(notice.url, '_blank')}>
            {notice.title}
          </NoticeItem>
        ))}
      </RollerList>
    </RollerContainer>
  );
};

export default NoticeRoller;
