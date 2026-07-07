// 공통 모달 접근성 훅 (요구사항 9.3, 9.4)
//
// - 포커스 트랩: 모달이 열려 있는 동안 Tab/Shift+Tab 포커스가 모달 내부에서
//   순환하도록 하여 포커스가 모달 밖으로 벗어나지 않게 한다(요구사항 9.3).
// - Escape: 모달이 열린 상태에서 Escape 키를 누르면 onClose를 호출한다(요구사항 9.4).
// - 열릴 때 첫 포커서블 요소로 포커스를 이동하고, 닫힐 때 모달을 연 트리거
//   요소로 포커스를 복귀시킨다.
//
// 포커스 트랩의 핵심 계산 로직은 순수 함수(getFocusableElements,
// getNextTrapFocus)로 분리하여 DOM 부수효과 없이 단위/속성 테스트가 가능하다.
import { useEffect, useRef } from 'react';

// 키보드로 포커스 가능한 요소를 선택하는 CSS 선택자.
const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

/**
 * 주어진 컨테이너 내부에서 실제로 포커스 가능한(보이는) 요소들을 순서대로 반환한다.
 * @param {HTMLElement|null} container 모달 컨테이너 요소
 * @returns {HTMLElement[]} 포커스 가능한 요소 배열
 */
export const getFocusableElements = (container) => {
  if (!container || typeof container.querySelectorAll !== 'function') {
    return [];
  }
  const nodes = Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR));
  return nodes.filter((el) => {
    if (el.hasAttribute('disabled')) return false;
    if (el.getAttribute('aria-hidden') === 'true') return false;
    // jsdom에서는 offsetParent/getClientRects가 제한적이므로 hidden 속성만 확인한다.
    if (el.hidden) return false;
    return true;
  });
};

/**
 * 포커스 트랩에서 다음에 포커스를 받아야 할 요소를 계산하는 순수 함수.
 *
 * 규칙(경계 순환):
 * - 마지막 요소에서 Tab(정방향) → 첫 요소로 순환한다.
 * - 첫 요소에서 Shift+Tab(역방향) → 마지막 요소로 순환한다.
 * - 그 외 내부 이동은 브라우저 기본 동작에 맡기기 위해 null을 반환한다.
 * - 활성 요소가 목록에 없으면(모달 밖) 방향에 맞는 경계 요소를 반환하여
 *   포커스를 모달 내부로 되돌린다.
 *
 * @param {HTMLElement[]} focusables 포커스 가능한 요소 배열(문서 순서)
 * @param {HTMLElement|null} activeElement 현재 포커스된 요소
 * @param {boolean} shiftKey Shift 키가 눌렸는지 여부(역방향 Tab)
 * @returns {HTMLElement|null} 포커스를 옮길 대상 요소, 또는 기본 동작 유지 시 null
 */
export const getNextTrapFocus = (focusables, activeElement, shiftKey) => {
  if (!Array.isArray(focusables) || focusables.length === 0) {
    return null;
  }

  const first = focusables[0];
  const last = focusables[focusables.length - 1];
  const currentIndex = focusables.indexOf(activeElement);

  if (shiftKey) {
    // 역방향: 첫 요소이거나 모달 밖이면 마지막 요소로 순환한다.
    if (currentIndex <= 0) {
      return last;
    }
    return null;
  }

  // 정방향: 마지막 요소이거나 모달 밖이면 첫 요소로 순환한다.
  if (currentIndex === -1 || currentIndex === focusables.length - 1) {
    return first;
  }
  return null;
};

/**
 * 모달 접근성(포커스 트랩 + Escape 닫기 + 포커스 복귀) 공통 훅.
 *
 * @param {boolean} isOpen 모달 열림 여부
 * @param {() => void} onClose 모달을 닫는 콜백(Escape 시 호출)
 * @returns {React.RefObject<HTMLElement>} 모달 컨테이너에 부착할 ref
 */
export const useModalA11y = (isOpen, onClose) => {
  const containerRef = useRef(null);
  // onClose가 매 렌더마다 새 함수로 전달되어도 효과가 재실행되어 포커스를
  // 빼앗지 않도록 최신 콜백을 ref에 보관하고, 효과는 isOpen에만 의존한다.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!isOpen) return undefined;

    const container = containerRef.current;
    if (!container) return undefined;

    // 모달을 연 트리거 요소를 기억하여 닫힐 때 포커스를 복귀시킨다.
    const triggerElement =
      typeof document !== 'undefined' ? document.activeElement : null;

    // 열릴 때 첫 포커서블로 포커스 이동(없으면 컨테이너 자체).
    const focusables = getFocusableElements(container);
    if (focusables.length > 0) {
      focusables[0].focus();
    } else if (typeof container.focus === 'function') {
      container.focus();
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        if (typeof onCloseRef.current === 'function') {
          onCloseRef.current();
        }
        return;
      }

      if (event.key === 'Tab') {
        const current = getFocusableElements(container);
        if (current.length === 0) {
          // 포커스 가능한 요소가 없으면 포커스가 밖으로 나가지 않도록 막는다.
          event.preventDefault();
          return;
        }
        const next = getNextTrapFocus(
          current,
          typeof document !== 'undefined' ? document.activeElement : null,
          event.shiftKey
        );
        if (next) {
          event.preventDefault();
          next.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      // 닫힐 때 트리거 요소로 포커스 복귀.
      if (triggerElement && typeof triggerElement.focus === 'function') {
        triggerElement.focus();
      }
    };
  }, [isOpen]);

  return containerRef;
};

export default useModalA11y;
