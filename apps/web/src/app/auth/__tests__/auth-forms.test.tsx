import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import LoginPage from '@/app/auth/login/page';
import RegisterPage from '@/app/auth/register/page';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
  }),
}));

vi.mock('@/components/providers/auth-provider', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('auth forms', () => {
  it('configures login form autocomplete best-effort attrs', () => {
    render(<LoginPage />);

    const form = document.querySelector('form[aria-label="Форма входа"]');
    const email = screen.getByLabelText('Email');
    const password = screen.getByLabelText('Пароль');

    expect(form).toHaveAttribute('autocomplete', 'off');
    expect(email).toHaveAttribute('autocomplete', 'username');
    expect(email).toHaveAttribute('autocapitalize', 'none');
    expect(email).toHaveAttribute('autocorrect', 'off');
    expect(password).toHaveAttribute('autocomplete', 'current-password');

    expect(document.querySelector('input[name="fake_username"]')).toBeInTheDocument();
    expect(document.querySelector('input[name="fake_password"]')).toBeInTheDocument();
  });

  it('uses new-password autocomplete on register form', () => {
    render(<RegisterPage />);

    const form = document.querySelector('form[aria-label="Форма регистрации"]');
    const password = screen.getByLabelText('Пароль');

    expect(form).toHaveAttribute('autocomplete', 'off');
    expect(password).toHaveAttribute('autocomplete', 'new-password');
  });
});
