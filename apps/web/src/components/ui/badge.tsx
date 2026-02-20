import { cn } from '@/lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: 'default' | 'success' | 'warning';
}

const toneMap: Record<NonNullable<BadgeProps['tone']>, string> = {
  default: 'border border-white/20 bg-white/10 text-slate-100',
  success: 'border border-emerald-300/25 bg-emerald-400/15 text-emerald-200',
  warning: 'border border-amber-300/30 bg-amber-300/15 text-amber-100',
};

export function Badge({ tone = 'default', className, ...props }: BadgeProps) {
  return (
    <span
      className={cn('inline-flex rounded-full px-2.5 py-1 text-xs font-medium tracking-wide', toneMap[tone], className)}
      {...props}
    />
  );
}
