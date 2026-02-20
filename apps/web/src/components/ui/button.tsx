import { ButtonHTMLAttributes, forwardRef } from 'react';

import { cn } from '@/lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variantMap: Record<ButtonVariant, string> = {
  primary: 'bg-violet-600 text-white hover:bg-violet-500',
  secondary: 'bg-slate-900 text-white hover:bg-slate-800',
  ghost: 'bg-transparent border border-slate-300 hover:bg-slate-100 text-slate-800',
  danger: 'bg-rose-600 text-white hover:bg-rose-500',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60',
        variantMap[variant],
        className,
      )}
      {...props}
    />
  ),
);

Button.displayName = 'Button';
