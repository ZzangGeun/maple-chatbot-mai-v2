import React from 'react';
import { getCategoryIcon } from '../../utils/communityUtils';

const CommunityWriteModal = ({
    setShowWriteModal,
    writeForm,
    setWriteForm,
    handleSubmitPost,
    categories
}) => {
    return (
        <div className="modal-overlay" onClick={() => setShowWriteModal(false)}>
            <div className="write-modal" onClick={(e) => e.stopPropagation()}>
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
