import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';

const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`;

const Container = styled.div`
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
`;

const ItemWrapper = styled.div`
  width: 100%;
  height: 100%;
  animation: ${fadeIn} 0.5s ease-in-out;
  display: flex; /* Ensure content is centered or laid out correctly */
  justify-content: center;
  align-items: center;
`;

const ImageRoller = ({ items, renderItem, interval = 3000 }) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        if (!items || items.length <= 1) return;

        const timer = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % items.length);
        }, interval);

        return () => clearInterval(timer);
    }, [items, interval]);

    if (!items || items.length === 0) {
        return <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>정보가 없습니다.</div>;
    }

    const currentItem = items[currentIndex];

    return (
        <Container>
            {/* Key change triggers re-mount and animation */}
            <ItemWrapper key={currentIndex}>
                {renderItem(currentItem)}
            </ItemWrapper>
        </Container>
    );
};

export default ImageRoller;
