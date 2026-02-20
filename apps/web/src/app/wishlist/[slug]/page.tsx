'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/auth-provider';
import { WishlistItemCard } from '@/components/wishlist/wishlist-item-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { publicApi } from '@/lib/api';
import { getGuestToken, setGuestToken } from '@/lib/guest-session';
import { useWishlistRealtime } from '@/hooks/use-wishlist-realtime';

export default function PublicWishlistPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [guestToken, setToken] = useState<string | null>(null);

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
    mutationFn: async () => {
      const name = window.prompt('??? ???? ??????');
      if (!name) {
        throw new Error('??? ???????????');
      }
      return publicApi.createGuestSession(slug, { name });
    },
    onSuccess: (response) => {
      setGuestToken(slug, response.token);
      setToken(response.token);
      toast.success('???????? ?????? ???????');
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : '?? ??????? ??????? ???????? ??????');
    },
  });

  const reserveMutation = useMutation({
    mutationFn: (itemId: string) => {
      if (!guestToken) throw new Error('??????? ?????? ???????? ??????');
      return publicApi.reserve(slug, itemId, guestToken);
    },
    onSuccess: () => {
      toast.success('??????? ??????????????');
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : '?????? ???????'),
  });

  const unreserveMutation = useMutation({
    mutationFn: (itemId: string) => {
      if (!guestToken) throw new Error('??????? ?????? ???????? ??????');
      return publicApi.unreserve(slug, itemId, guestToken);
    },
    onSuccess: () => {
      toast.success('?????? ????');
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : '?????? ?????? ???????'),
  });

  const contributeMutation = useMutation({
    mutationFn: (itemId: string) => {
      if (!guestToken) throw new Error('??????? ?????? ???????? ??????');
      const amount = window.prompt('????? ??????');
      if (!amount) throw new Error('????? ???????????');
      return publicApi.contribute(slug, itemId, guestToken, amount);
    },
    onSuccess: () => {
      toast.success('????? ????????');
      queryClient.invalidateQueries({ queryKey: ['public-wishlist', slug] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : '?????? ??????'),
  });

  const wishlist = wishlistQuery.data;

  const canActAsGuest = useMemo(
    () => wishlist?.viewer_kind !== 'owner' && Boolean(guestToken),
    [wishlist?.viewer_kind, guestToken],
  );

  if (wishlistQuery.isLoading) {
    return <div className='mx-auto max-w-5xl px-4 py-8 text-slate-600'>????????? ??????...</div>;
  }

  if (wishlistQuery.isError || !wishlist) {
    return (
      <div className='mx-auto max-w-5xl px-4 py-8'>
        <Card>
          <CardContent className='py-10 text-center text-slate-600'>
            ?? ??????? ??????? ??????. ??????? ??????.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className='mx-auto max-w-5xl space-y-6 px-4 py-8'>
      <Card>
        <CardHeader>
          <CardTitle>{wishlist.title}</CardTitle>
          <p className='text-sm text-slate-600'>{wishlist.description || '???????? ?? ?????????'}</p>
        </CardHeader>
        <CardContent className='space-y-3'>
          <p className='text-sm text-slate-500'>
            ??????: <span className='font-medium text-slate-800'>{wishlist.status}</span>
          </p>

          {wishlist.viewer_kind === 'owner' && user && (
            <p className='rounded-xl bg-violet-50 p-3 text-sm text-violet-700'>
              ??? ???? ??????. ??? ?????????? ?????? ???????.
            </p>
          )}

          {wishlist.viewer_kind !== 'owner' && !canActAsGuest && (
            <Button onClick={() => createGuestSessionMutation.mutate()} disabled={createGuestSessionMutation.isPending}>
              ????????????? ? ??????? ???????
            </Button>
          )}
        </CardContent>
      </Card>

      <div className='grid gap-4'>
        {wishlist.items.length > 0 ? (
          wishlist.items.map((item) => (
            <WishlistItemCard
              key={item.id}
              item={item}
              currency={wishlist.currency}
              ownerView={wishlist.viewer_kind === 'owner'}
              onReserve={(itemId) => reserveMutation.mutate(itemId)}
              onUnreserve={(itemId) => unreserveMutation.mutate(itemId)}
              onContribute={(itemId) => contributeMutation.mutate(itemId)}
              loading={reserveMutation.isPending || unreserveMutation.isPending || contributeMutation.isPending}
            />
          ))
        ) : (
          <Card>
            <CardContent className='py-10 text-center text-slate-600'>
              ???? ????? ??? ????????.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
