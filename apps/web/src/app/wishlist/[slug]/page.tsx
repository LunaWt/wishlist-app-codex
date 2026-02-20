'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/auth-provider';
import { WishlistItemCard } from '@/components/wishlist/wishlist-item-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useWishlistRealtime } from '@/hooks/use-wishlist-realtime';
import { publicApi } from '@/lib/api';
import { getGuestToken, setGuestToken } from '@/lib/guest-session';

export default function PublicWishlistPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [guestToken, setToken] = useState<string | null>(null);
  const [guestName, setGuestName] = useState('');
  const [contributionItemId, setContributionItemId] = useState<string | null>(null);
  const [contributionAmount, setContributionAmount] = useState('');

  useEffect(() => {
    if (!slug) return;
    setToken(getGuestToken(slug));
  }, [slug]);

  const wishlistQuery = useQuery({
    queryKey: ['public-wishlist', slug, guestToken],
    queryFn: () => publicApi.getWishlist(slug, guestToken ?? undefined),
    enabled: Boolean(slug),
  });

  useWishlistRealtime({
    shareSlug: slug,
    onEvent: () => {
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
  });

  const createGuestSessionMutation = useMutation({
    mutationFn: async (name: string) => publicApi.createGuestSession(slug, { name }),
    onSuccess: (response) => {
      setGuestToken(slug, response.token);
      setToken(response.token);
      setGuestName('');
      toast.success('Гостевой доступ активирован');
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Не удалось создать гостевую сессию');
    },
  });

  const reserveMutation = useMutation({
    mutationFn: (itemId: string) => {
      if (!guestToken) throw new Error('Сначала включи гостевой режим');
      return publicApi.reserve(slug, itemId, guestToken);
    },
    onSuccess: () => {
      toast.success('Подарок зарезервирован');
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : 'Ошибка резерва'),
  });

  const unreserveMutation = useMutation({
    mutationFn: (itemId: string) => {
      if (!guestToken) throw new Error('Сначала включи гостевой режим');
      return publicApi.unreserve(slug, itemId, guestToken);
    },
    onSuccess: () => {
      toast.success('Резерв снят');
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : 'Ошибка снятия резерва'),
  });

  const contributeMutation = useMutation({
    mutationFn: ({ itemId, amount }: { itemId: string; amount: string }) => {
      if (!guestToken) throw new Error('Сначала включи гостевой режим');
      return publicApi.contribute(slug, itemId, guestToken, amount);
    },
    onSuccess: () => {
      toast.success('Вклад добавлен');
      setContributionAmount('');
      setContributionItemId(null);
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : 'Ошибка вклада'),
  });

  const wishlist = wishlistQuery.data;

  const canActAsGuest = useMemo(
    () => wishlist?.viewer_kind !== 'owner' && Boolean(guestToken),
    [wishlist?.viewer_kind, guestToken],
  );

  if (wishlistQuery.isLoading) {
    return <div className='mx-auto max-w-5xl px-4 py-8 text-slate-300'>Загружаем вишлист…</div>;
  }

  if (wishlistQuery.isError || !wishlist) {
    return (
      <div className='mx-auto max-w-5xl px-4 py-8'>
        <Card>
          <CardContent className='py-10 text-center text-slate-300'>
            Не удалось открыть список. Проверь ссылку и попробуй ещё раз.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className='mx-auto max-w-5xl space-y-6 px-4 py-8'>
      <Card className='animate-enter'>
        <CardHeader>
          <CardTitle>{wishlist.title}</CardTitle>
          <p className='text-sm text-slate-300'>{wishlist.description || 'Описание не добавлено'}</p>
        </CardHeader>

        <CardContent className='space-y-4'>
          <p className='text-sm text-slate-300'>
            Статус списка: <span className='font-semibold text-white'>{wishlist.status}</span>
          </p>

          {wishlist.viewer_kind === 'owner' && user && (
            <p className='rounded-2xl border border-brand-300/30 bg-brand-500/15 p-3 text-sm text-brand-100'>
              Это твой собственный список. Здесь отображается owner-режим без персоналий гостей.
            </p>
          )}

          {wishlist.viewer_kind !== 'owner' && !canActAsGuest && (
            <form
              className='flex flex-col gap-2 sm:flex-row'
              onSubmit={(event) => {
                event.preventDefault();
                const normalized = guestName.trim();
                if (normalized.length < 2) {
                  toast.error('Введи имя от 2 символов');
                  return;
                }
                createGuestSessionMutation.mutate(normalized);
              }}
            >
              <Input
                placeholder='Как тебя подписать в этом списке?'
                value={guestName}
                onChange={(event) => setGuestName(event.target.value)}
              />
              <Button type='submit' disabled={createGuestSessionMutation.isPending}>
                Включить гостевой режим
              </Button>
            </form>
          )}
        </CardContent>
      </Card>

      <div className='grid gap-4'>
        {wishlist.items.length > 0 ? (
          wishlist.items.map((item) => (
            <div key={item.id} className='space-y-2'>
              <WishlistItemCard
                item={item}
                currency={wishlist.currency}
                ownerView={wishlist.viewer_kind === 'owner'}
                onReserve={(itemId) => reserveMutation.mutate(itemId)}
                onUnreserve={(itemId) => unreserveMutation.mutate(itemId)}
                onContribute={(itemId) => {
                  setContributionItemId((current) => (current === itemId ? null : itemId));
                }}
                loading={reserveMutation.isPending || unreserveMutation.isPending || contributeMutation.isPending}
              />

              {contributionItemId === item.id && wishlist.viewer_kind !== 'owner' && (
                <Card className='animate-enter'>
                  <CardContent className='space-y-3'>
                    <p className='text-sm text-slate-200'>Укажи сумму вклада для «{item.title}»</p>

                    <form
                      className='flex flex-col gap-2 sm:flex-row'
                      onSubmit={(event) => {
                        event.preventDefault();
                        const normalized = contributionAmount.trim();
                        if (!normalized) {
                          toast.error('Укажи сумму');
                          return;
                        }
                        contributeMutation.mutate({ itemId: item.id, amount: normalized });
                      }}
                    >
                      <Input
                        placeholder='Например, 1500'
                        value={contributionAmount}
                        onChange={(event) => setContributionAmount(event.target.value)}
                        inputMode='decimal'
                      />
                      <Button type='submit' disabled={contributeMutation.isPending}>
                        Подтвердить вклад
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              )}
            </div>
          ))
        ) : (
          <Card>
            <CardContent className='py-10 text-center text-slate-300'>Пока подарков нет.</CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
