import { cn } from '@/lib/utils';

interface ProgressProps {
  value: number;
  className?: string;
}

export function Progress({ value, className }: ProgressProps) {
  const safe = Math.max(0, Math.min(100, value));
  return (
    <div className={cn('h-2 w-full rounded-full bg-slate-200', className)}>
      <div
        className='h-2 rounded-full bg-emerald-500 transition-all duration-500'
        style={{ width: `${safe}%` }}
      />
    </div>
  );
}
