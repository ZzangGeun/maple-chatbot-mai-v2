import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import '../../styles/components/auth.css';

const SignupPopup = () => {
    const { isSignupModalOpen, closeSignupModal, openLoginModal, register, error, isLoading } = useAuth();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        password_confirm: '',
    });
    const [localError, setLocalError] = useState('');

    // 모달이 열릴 때 입력창 초기화
    useEffect(() => {
        if (isSignupModalOpen) {
            setFormData({
                username: '',
                email: '',
                password: '',
                password_confirm: '',
            });
            setLocalError('');
        }
    }, [isSignupModalOpen]);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setLocalError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // 비밀번호 확인 체크
        if (formData.password !== formData.password_confirm) {
            setLocalError('비밀번호가 일치하지 않습니다.');
            return;
        }

        // 비밀번호 길이 체크
        if (formData.password.length < 6) {
            setLocalError('비밀번호는 6자 이상이어야 합니다.');
            return;
        }

        const result = await register({
            username: formData.username,
            email: formData.email,
            password: formData.password,
        });

        if (result.success) {
            // 회원가입 성공 시 로그인 팝업으로 전환
            closeSignupModal();
            openLoginModal();
        }
    };

    const handleSwitchToLogin = (e) => {
        e.preventDefault();
        closeSignupModal();
        openLoginModal();
    };

    if (!isSignupModalOpen) return null;

    return (
        <div className="login-popup-overlay" onClick={closeSignupModal}>
            <div className="login-popup-modal" onClick={(e) => e.stopPropagation()}>
                <div className="login-popup-header">
                    <h3>회원가입</h3>
                    <button className="login-popup-close" onClick={closeSignupModal}>&times;</button>
                </div>

                <div className="login-popup-content">
                    {(error || localError) && (
                        <div style={{ color: '#dc3545', marginBottom: '15px', fontSize: '14px', textAlign: 'center' }}>
                            {localError || error}
                        </div>
                    )}

                    <form className="login-popup-form" onSubmit={handleSubmit}>
                        <div className="login-input-group">
                            <label htmlFor="signupUsername">아이디</label>
                            <input
                                type="text"
                                id="signupUsername"
                                name="username"
                                className="login-popup-input"
                                placeholder="아이디를 입력하세요"
                                value={formData.username}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="login-input-group">
                            <label htmlFor="signupEmail">이메일</label>
                            <input
                                type="email"
                                id="signupEmail"
                                name="email"
                                className="login-popup-input"
                                placeholder="이메일을 입력하세요"
                                value={formData.email}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="login-input-group">
                            <label htmlFor="signupPassword">비밀번호</label>
                            <input
                                type="password"
                                id="signupPassword"
                                name="password"
                                className="login-popup-input"
                                placeholder="비밀번호를 입력하세요 (6자 이상)"
                                value={formData.password}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="login-input-group">
                            <label htmlFor="signupPasswordConfirm">비밀번호 확인</label>
                            <input
                                type="password"
                                id="signupPasswordConfirm"
                                name="password_confirm"
                                className="login-popup-input"
                                placeholder="비밀번호를 다시 입력하세요"
                                value={formData.password_confirm}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <button type="submit" className="login-popup-btn" disabled={isLoading}>
                            {isLoading ? '가입 중...' : '회원가입'}
                        </button>
                    </form>

                    <div className="login-popup-links" style={{ marginTop: '20px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>이미 계정이 있으신가요?</span>
                        <a href="#" className="login-link" onClick={handleSwitchToLogin} style={{ marginLeft: '8px' }}>
                            로그인
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SignupPopup;
