'use client';

import Link from 'next/link';
import { Archive, Gift, HandCoins, LinkIcon, Lock, Unlock } from 'lucide-react';

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
    <Card className='animate-enter overflow-hidden'>
      <CardContent className='space-y-4'>
        <div className='flex items-start justify-between gap-3'>
          <div className='space-y-1'>
            <h4 className='text-lg font-semibold text-white'>{item.title}</h4>
            {item.notes && <p className='text-sm text-slate-300'>{item.notes}</p>}
          </div>

          <Badge tone={item.is_reserved ? 'warning' : 'success'}>
            {item.is_reserved ? 'Зарезервирован' : 'Свободен'}
          </Badge>
        </div>

        {item.image_url ? (
          <img src={item.image_url} alt={item.title} className='h-48 w-full rounded-2xl object-cover' />
        ) : (
          <div className='flex h-40 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-slate-400'>
            <Gift className='h-5 w-5' />
          </div>
        )}

        <div className='flex flex-wrap items-center gap-3 text-sm text-slate-300'>
          {item.price && <span>Цена: {formatMoney(item.price, currency)}</span>}
          {item.product_url && (
            <Link href={item.product_url} target='_blank' className='inline-flex items-center gap-1 text-cyan-300 hover:text-cyan-200'>
              <LinkIcon className='h-3.5 w-3.5' />
              Перейти к товару
            </Link>
          )}
        </div>

        {isGroup && (
          <div className='space-y-2 rounded-2xl border border-white/10 bg-white/5 p-3'>
            <div className='flex items-center justify-between text-sm'>
              <span className='text-slate-300'>Собрано</span>
              <span className='font-semibold text-white'>
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
                <Lock className='h-4 w-4' />
                Забронировать
              </Button>
            )}

            {!isGroup && isGuestItem(item) && item.reserved_by_you && onUnreserve && (
              <Button variant='ghost' disabled={loading} onClick={() => onUnreserve(item.id)}>
                <Unlock className='h-4 w-4' />
                Снять резерв
              </Button>
            )}

            {isGroup && onContribute && (
              <Button variant='secondary' disabled={loading} onClick={() => onContribute(item.id)}>
                <HandCoins className='h-4 w-4' />
                Внести вклад
              </Button>
            )}
          </div>
        )}

        {ownerView && onArchive && item.status !== 'archived' && (
          <Button variant='ghost' onClick={() => onArchive(item.id)}>
            <Archive className='h-4 w-4' />
            Архивировать
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
