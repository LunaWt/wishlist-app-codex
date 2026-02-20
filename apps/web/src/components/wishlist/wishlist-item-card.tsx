'use client';

import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { GuestItemView, OwnerItemView } from '@/lib/contracts';
import { formatMoney, safePercent } from '@/lib/utils';

type WishlistItem = OwnerItemView | GuestItemView;

interface WishlistItemCardProps {
  item: WishlistItem;
  currency: string;
  onReserve?: (itemId: string) => void;
  onUnreserve?: (itemId: string) => void;
  onContribute?: (itemId: string) => void;
  onArchive?: (itemId: string) => void;
  loading?: boolean;
  ownerView?: boolean;
}

function isGuestItem(item: WishlistItem): item is GuestItemView {
  return 'reserved_by_you' in item;
}

export function WishlistItemCard({
  item,
  currency,
  onReserve,
  onUnreserve,
  onContribute,
  onArchive,
  loading,
  ownerView,
}: WishlistItemCardProps) {
  const progressValue = safePercent(item.progress_percent);
  const isGroup = item.mode === 'group';

  return (
    <Card className='overflow-hidden'>
      <CardContent className='space-y-3'>
        <div className='flex items-start justify-between gap-3'>
          <div className='space-y-1'>
            <h4 className='font-semibold text-slate-900'>{item.title}</h4>
            {item.notes && <p className='text-sm text-slate-600'>{item.notes}</p>}
          </div>
          <Badge tone={item.is_reserved ? 'warning' : 'default'}>
            {item.is_reserved ? 'Зарезервирован' : 'Свободен'}
          </Badge>
        </div>

        {item.image_url && (
          <img
            src={item.image_url}
            alt={item.title}
            className='h-44 w-full rounded-xl object-cover'
          />
        )}

        <div className='flex flex-wrap items-center gap-2 text-sm text-slate-600'>
          {item.price && <span>Цена: {formatMoney(item.price, currency)}</span>}
          {item.product_url && (
            <Link href={item.product_url} className='text-violet-600 hover:underline' target='_blank'>
              Ссылка на товар
            </Link>
          )}
        </div>

        {isGroup && (
          <div className='space-y-2 rounded-xl bg-slate-50 p-3'>
            <div className='flex items-center justify-between text-sm'>
              <span className='text-slate-600'>Собрано</span>
              <span className='font-semibold'>
                {formatMoney(item.collected_amount, currency)} / {formatMoney(item.target_amount ?? item.price ?? 0, currency)}
              </span>
            </div>
            <Progress value={progressValue} />
          </div>
        )}

        {!ownerView && (
          <div className='flex flex-wrap gap-2'>
            {!isGroup && onReserve && !item.is_reserved && (
              <Button disabled={loading} onClick={() => onReserve(item.id)}>
                Забронировать
              </Button>
            )}
            {!isGroup && isGuestItem(item) && item.reserved_by_you && onUnreserve && (
              <Button variant='ghost' disabled={loading} onClick={() => onUnreserve(item.id)}>
                Снять резерв
              </Button>
            )}
            {isGroup && onContribute && (
              <Button disabled={loading} onClick={() => onContribute(item.id)}>
                Внести вклад
              </Button>
            )}
          </div>
        )}

        {ownerView && onArchive && item.status !== 'archived' && (
          <Button variant='ghost' onClick={() => onArchive(item.id)}>
            Архивировать
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
