import React, { useCallback } from 'react';
import { getCategoryIcon } from '../../utils/communityUtils';
import { useModalA11y } from '../../hooks/useModalA11y';

const CommunityWriteModal = ({
    setShowWriteModal,
    writeForm,
    setWriteForm,
    handleSubmitPost,
    categories
}) => {
    // 이 모달은 부모가 조건부로 마운트하므로, 마운트되어 있는 동안 항상 열린 상태다.
    const closeModal = useCallback(() => setShowWriteModal(false), [setShowWriteModal]);
    // 모달 접근성: 포커스 트랩 + Escape 닫기 + 포커스 복귀 (요구사항 9.3, 9.4)
    const modalRef = useModalA11y(true, closeModal);

    return (
        <div className="modal-overlay" onClick={() => setShowWriteModal(false)}>
            <div className="write-modal" ref={modalRef} role="dialog" aria-modal="true" aria-label="게시글 작성" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>게시글 작성</h2>
                    <button className="close-btn" onClick={() => setShowWriteModal(false)}>×</button>
                </div>

                <form className="write-form" onSubmit={handleSubmitPost}>
                    <div className="form-group">
                        <label>카테고리</label>
                        <select
                            value={writeForm.category}
                            onChange={(e) => setWriteForm({ ...writeForm, category: e.target.value })}
                            className="category-select"
                        >
                            {categories.filter(c => c.id !== 'all').map(category => (
                                <option key={category.id} value={category.id}>
                                    {getCategoryIcon(category.id)} {category.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>제목</label>
                        <input
                            type="text"
                            value={writeForm.title}
                            onChange={(e) => setWriteForm({ ...writeForm, title: e.target.value })}
                            placeholder="제목을 입력하세요"
                            required
                            className="title-input"
                        />
                    </div>

                    <div className="form-group">
                        <label>내용</label>
                        <textarea
                            value={writeForm.content}
                            onChange={(e) => setWriteForm({ ...writeForm, content: e.target.value })}
                            placeholder="내용을 입력하세요"
                            required
                            className="content-textarea"
                            rows="10"
                        />
                    </div>

                    <div className="form-actions">
                        <button type="button" className="cancel-btn" onClick={() => setShowWriteModal(false)}>
                            취소
                        </button>
                        <button type="submit" className="submit-btn">
                            작성 완료
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CommunityWriteModal;
