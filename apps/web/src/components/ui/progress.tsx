import { cn } from '@/lib/utils';

interface ProgressProps {
  value: number;
  className?: string;
}

export function Progress({ value, className }: ProgressProps) {
  const safe = Math.max(0, Math.min(100, value));

  return (
    <div className={cn('h-2.5 w-full overflow-hidden rounded-full bg-white/10', className)}>
      <div
        className='h-full rounded-full bg-gradient-to-r from-emerald-400 via-cyan-400 to-brand-500 transition-all duration-500'
        style={{ width: `${safe}%` }}
      />
    </div>
  );
}
