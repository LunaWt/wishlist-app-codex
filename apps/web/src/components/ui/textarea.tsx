import { TextareaHTMLAttributes, forwardRef } from 'react';

import { cn } from '@/lib/utils';

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'w-full rounded-2xl border border-white/15 bg-slate-950/55 px-3.5 py-2.5 text-sm text-slate-100 outline-none transition-all duration-200 placeholder:text-slate-400/80 focus:border-brand-400 focus:ring-2 focus:ring-brand-400/25',
        className,
      )}
      {...props}
    />
  ),
);

Textarea.displayName = 'Textarea';
