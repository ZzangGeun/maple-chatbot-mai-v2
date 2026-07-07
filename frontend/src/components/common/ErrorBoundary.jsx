import React from 'react';
import '../../styles/components/common.css';

/**
 * 렌더링 중 발생한 예외를 포착하여 대체 UI를 표시하는 Error Boundary입니다.
 *
 * `getDerivedStateFromError`로 오류 상태를 갱신하고, `componentDidCatch`에서
 * 오류를 로깅합니다. 자식 트리에서 예외가 발생해도 애플리케이션 전체가
 * 중단되지 않도록 대체 오류 UI를 렌더합니다.
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - 보호할 자식 트리
 * @param {React.ReactNode|Function} [props.fallback] - 커스텀 대체 UI.
 *   함수인 경우 `(error, reset) => ReactNode` 형태로 호출됩니다.
 * @param {Function} [props.onError] - 오류 포착 시 호출되는 콜백 `(error, errorInfo)`
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
    this.handleReset = this.handleReset.bind(this);
  }

  static getDerivedStateFromError(error) {
    // 다음 렌더에서 대체 UI를 표시하도록 상태를 갱신합니다.
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // 오류를 콘솔에 기록하고, 제공된 경우 외부 콜백에 전달합니다.
    console.error('ErrorBoundary가 렌더링 예외를 포착했습니다:', error, errorInfo);
    if (typeof this.props.onError === 'function') {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset() {
    // 오류 상태를 초기화하여 자식 트리를 다시 렌더링합니다.
    this.setState({ hasError: false, error: null });
  }

  render() {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      if (typeof fallback === 'function') {
        return fallback(error, this.handleReset);
      }
      if (fallback) {
        return fallback;
      }

      return (
        <div className="error-boundary" role="alert">
          <span className="error-boundary__icon" aria-hidden="true">⚠️</span>
          <h2 className="error-boundary__title">문제가 발생했습니다</h2>
          <p className="error-boundary__message">
            페이지를 표시하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.
          </p>
          {error && (
            <details className="error-boundary__details">
              <summary>오류 상세 정보</summary>
              <pre className="error-boundary__stack">
                {error.message || String(error)}
              </pre>
            </details>
          )}
          <button
            type="button"
            className="error-boundary__retry"
            onClick={this.handleReset}
          >
            다시 시도
          </button>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
