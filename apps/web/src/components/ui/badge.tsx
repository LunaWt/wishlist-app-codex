import { cn } from '@/lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: 'default' | 'success' | 'warning';
}

export function Badge({ tone = 'default', className, ...props }: BadgeProps) {
  const toneMap = {
    default: 'bg-slate-100 text-slate-700',
    success: 'bg-emerald-100 text-emerald-700',
    warning: 'bg-amber-100 text-amber-700',
  };

  return (
    <span
      className={cn('inline-flex rounded-full px-2.5 py-1 text-xs font-medium', toneMap[tone], className)}
      {...props}
    />
  );
}
