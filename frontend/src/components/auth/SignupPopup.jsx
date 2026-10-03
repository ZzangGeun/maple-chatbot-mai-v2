import React, { useState, useEffect } from 'react';
import { ArrowRight, Leaf, Loader2, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useModalA11y } from '../../hooks/useModalA11y';
import '../../styles/components/auth.css';

const emptyForm = {
    username: '',
    password: '',
    confirm_password: '',
    maple_nickname: '',
    nexon_api_key: '',
};

const SignupPopup = () => {
    const { isSignupModalOpen, closeSignupModal, openLoginModal, register, error, isLoading } = useAuth();
    const modalRef = useModalA11y(isSignupModalOpen, closeSignupModal);
    const [formData, setFormData] = useState({ ...emptyForm });
    const [localError, setLocalError] = useState('');

    useEffect(() => {
        if (isSignupModalOpen) {
            setFormData({ ...emptyForm });
            setLocalError('');
        }
    }, [isSignupModalOpen]);

    const handleChange = (e) => {
        setFormData(current => ({ ...current, [e.target.name]: e.target.value }));
        setLocalError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (isLoading) return;

        const username = formData.username.trim();
        if (!/^[a-zA-Z0-9_]{6,20}$/.test(username)) {
            setLocalError('아이디는 6~20자의 영문자, 숫자, 밑줄(_)로 입력해주세요.');
            return;
        }
        if (formData.password.length < 8) {
            setLocalError('비밀번호는 8자 이상 입력해주세요.');
            return;
        }
        if (formData.password !== formData.confirm_password) {
            setLocalError('비밀번호와 비밀번호 확인이 일치하지 않습니다.');
            return;
        }
        if (!formData.maple_nickname.trim() || !formData.nexon_api_key.trim()) {
            setLocalError('캐릭터 닉네임과 넥슨 API 키를 입력해주세요.');
            return;
        }

        const result = await register({
            username,
            password: formData.password,
            confirm_password: formData.confirm_password,
            maple_nickname: formData.maple_nickname.trim(),
            nexon_api_key: formData.nexon_api_key.trim(),
        });

        if (result.success) {
            closeSignupModal();
            openLoginModal();
        }
    };

    const handleSwitchToLogin = () => {
        closeSignupModal();
        openLoginModal();
    };

    if (!isSignupModalOpen) return null;

    return (
        <div className="login-popup-overlay" onClick={closeSignupModal}>
            <div className="login-popup-modal auth-signup-modal" ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="signupTitle" aria-describedby="signupDescription" onClick={(e) => e.stopPropagation()}>
                <div className="login-popup-header">
                    <div><span className="auth-eyebrow"><Leaf size={14} aria-hidden="true" /> YOUR NEW ADVENTURE</span><h2 id="signupTitle">나만의 모험 노트 만들기</h2></div>
                    <button type="button" className="login-popup-close" onClick={closeSignupModal} aria-label="회원가입 닫기"><X size={19} aria-hidden="true" /></button>
                </div>

                <div className="login-popup-content">
                    <p className="auth-modal-description" id="signupDescription">내 캐릭터를 연결하고, 메이와의 대화를 이어가세요.</p>
                    {(error || localError) && (
                        <div className="auth-error" role="alert">{localError || error}</div>
                    )}

                    <form className="login-popup-form" onSubmit={handleSubmit} aria-busy={isLoading}>
                        <div className="login-input-group">
                            <label htmlFor="signupUsername">아이디</label>
                            <input
                                type="text"
                                id="signupUsername"
                                name="username"
                                className="login-popup-input"
                                placeholder="사용할 아이디"
                                value={formData.username}
                                onChange={handleChange}
                                autoComplete="username"
                                minLength={6}
                                maxLength={20}
                                pattern="[A-Za-z0-9_]{6,20}"
                                aria-describedby="signupUsernameHelp"
                                required
                            />
                            <p className="auth-field-help" id="signupUsernameHelp">영문자, 숫자, 밑줄(_)로 6~20자 입력해주세요.</p>
                        </div>

                        <div className="login-input-group">
                            <label htmlFor="signupPassword">비밀번호</label>
                            <input
                                type="password"
                                id="signupPassword"
                                name="password"
                                className="login-popup-input"
                                placeholder="8자 이상 입력해주세요"
                                value={formData.password}
                                onChange={handleChange}
                                autoComplete="new-password"
                                minLength={8}
                                required
                            />
                        </div>

                        <div className="login-input-group">
                            <label htmlFor="signupPasswordConfirm">비밀번호 확인</label>
                            <input
                                type="password"
                                id="signupPasswordConfirm"
                                name="confirm_password"
                                className="login-popup-input"
                                placeholder="비밀번호를 한 번 더 입력해주세요"
                                value={formData.confirm_password}
                                onChange={handleChange}
                                autoComplete="new-password"
                                minLength={8}
                                required
                            />
                        </div>

                        <div className="login-input-group">
                            <label htmlFor="signupMapleNickname">캐릭터 닉네임</label>
                            <input
                                type="text"
                                id="signupMapleNickname"
                                name="maple_nickname"
                                className="login-popup-input"
                                placeholder="메이플스토리 대표 캐릭터 닉네임"
                                value={formData.maple_nickname}
                                onChange={handleChange}
                                autoComplete="off"
                                aria-describedby="signupMapleNicknameHelp"
                                required
                            />
                            <p className="auth-field-help" id="signupMapleNicknameHelp">연결할 넥슨 계정에서 가장 레벨이 높은 캐릭터를 입력해주세요.</p>
                        </div>

                        <div className="login-input-group">
                            <label htmlFor="signupNexonApiKey">넥슨 API 키</label>
                            <input
                                type="password"
                                id="signupNexonApiKey"
                                name="nexon_api_key"
                                className="login-popup-input"
                                placeholder="발급받은 메이플스토리 API 키"
                                value={formData.nexon_api_key}
                                onChange={handleChange}
                                autoComplete="off"
                                spellCheck={false}
                                aria-describedby="signupNexonApiKeyHelp"
                                required
                            />
                            <p className="auth-field-help" id="signupNexonApiKeyHelp">넥슨 Open API 개발자 센터에서 발급한 키로 대표 캐릭터를 확인합니다.</p>
                        </div>

                        <button type="submit" className="login-popup-btn" disabled={isLoading}>
                            {isLoading ? <Loader2 className="auth-loading-icon" size={18} aria-hidden="true" /> : <ArrowRight size={18} aria-hidden="true" />}{isLoading ? '캐릭터 확인 중…' : '회원가입'}
                        </button>
                    </form>

                    <div className="auth-signup-prompt">
                        <span>이미 계정이 있으신가요?</span>
                        <button type="button" className="login-link" onClick={handleSwitchToLogin}>로그인 <ArrowRight size={13} aria-hidden="true" /></button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SignupPopup;
