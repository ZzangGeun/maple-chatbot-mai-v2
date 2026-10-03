import React, { useCallback, useState } from 'react';
import { AlertCircle as CircleAlert, Loader2, PencilLine, Send, X } from 'lucide-react';
import { getCategoryIcon } from '../../utils/communityUtils';
import { useModalA11y } from '../../hooks/useModalA11y';

const CommunityWriteModal = ({ setShowWriteModal, writeForm, setWriteForm, handleSubmitPost, categories, submitError }) => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const closeModal = useCallback(() => setShowWriteModal(false), [setShowWriteModal]);
    const modalRef = useModalA11y(true, closeModal);
    const submitPost = async (event) => {
        event.preventDefault();
        if (isSubmitting || !writeForm.title.trim() || !writeForm.content.trim()) return;
        setIsSubmitting(true);
        try { await handleSubmitPost(event); } finally { setIsSubmitting(false); }
    };

    return (
        <div className="community-write-overlay" onClick={closeModal}>
            <div className="community-write-modal" ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="community-write-title" onClick={(event) => event.stopPropagation()}>
                <div className="community-modal-header"><div><span className="community-modal-eyebrow"><PencilLine size={14} aria-hidden="true" /> NEW STORY</span><h2 id="community-write-title">새로운 이야기를 나눠주세요</h2><p>당신의 경험이 누군가에게 도움이 될 거예요.</p></div><button type="button" className="community-close-btn" aria-label="게시글 작성 닫기" onClick={closeModal}><X size={20} aria-hidden="true" /></button></div>
                <form className="community-write-form" onSubmit={submitPost}>
                    <div className="community-form-group"><label htmlFor="post-category">카테고리</label><select id="post-category" value={writeForm.category} onChange={(event) => setWriteForm({ ...writeForm, category: event.target.value })} className="community-category-select">{categories.filter(category => category.id !== 'all').map(category => <option key={category.id} value={category.id}>{getCategoryIcon(category.id)} {category.name}</option>)}</select></div>
                    <div className="community-form-group"><label htmlFor="post-title">제목</label><input id="post-title" type="text" value={writeForm.title} onChange={(event) => setWriteForm({ ...writeForm, title: event.target.value })} placeholder="어떤 이야기를 나눌까요?" required className="community-title-input" /></div>
                    <div className="community-form-group"><label htmlFor="post-content">내용</label><textarea id="post-content" value={writeForm.content} onChange={(event) => setWriteForm({ ...writeForm, content: event.target.value })} placeholder="모험가님들과 나누고 싶은 이야기를 자유롭게 적어주세요." required className="community-content-textarea" rows="8" /></div>
                    {submitError && <div className="community-submit-error" role="alert"><CircleAlert size={16} aria-hidden="true" />{submitError}</div>}
                    <div className="community-form-actions"><button type="button" className="community-cancel-btn" onClick={closeModal}>취소</button><button type="submit" className="community-submit-btn" disabled={isSubmitting || !writeForm.title.trim() || !writeForm.content.trim()}>{isSubmitting ? <Loader2 className="community-loading-icon" size={16} aria-hidden="true" /> : <Send size={16} aria-hidden="true" />}{isSubmitting ? '등록 중' : '이야기 등록'}</button></div>
                </form>
            </div>
        </div>
    );
};

export default CommunityWriteModal;
