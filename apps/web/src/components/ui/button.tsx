import { ButtonHTMLAttributes, forwardRef } from 'react';

import { cn } from '@/lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variantMap: Record<ButtonVariant, string> = {
  primary:
    'bg-gradient-to-r from-brand-600 via-violet-500 to-cyan-500 text-white shadow-[0_12px_32px_-18px_rgba(56,189,248,0.9)] hover:-translate-y-0.5 hover:brightness-110 active:translate-y-0',
  secondary:
    'border border-white/20 bg-white/10 text-slate-100 hover:-translate-y-0.5 hover:bg-white/15',
  ghost:
    'border border-white/12 bg-transparent text-slate-200 hover:bg-white/10',
  danger:
    'bg-gradient-to-r from-rose-600 to-pink-600 text-white hover:-translate-y-0.5 hover:brightness-110',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60',
        variantMap[variant],
        className,
      )}
      {...props}
    />
  ),
);

Button.displayName = 'Button';
