'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Copy, Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/auth-provider';
import { WishlistItemCard } from '@/components/wishlist/wishlist-item-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { utilityApi, wishlistApi } from '@/lib/api';

interface WishlistFormValues {
  title: string;
  description: string;
  occasion: string;
  event_date: string;
}

interface ItemFormValues {
  title: string;
  product_url: string;
  image_url: string;
  notes: string;
  price: string;
  mode: 'single' | 'group';
  target_amount: string;
}

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const { user, loading } = useAuth();
  const [selectedWishlistId, setSelectedWishlistId] = useState<string | null>(null);

  const wishlistForm = useForm<WishlistFormValues>({
    defaultValues: {
      title: '',
      description: '',
      occasion: '',
      event_date: '',
    },
  });

  const itemForm = useForm<ItemFormValues>({
    defaultValues: {
      title: '',
      product_url: '',
      image_url: '',
      notes: '',
      price: '',
      mode: 'single',
      target_amount: '',
    },
  });

  const wishlistsQuery = useQuery({
    queryKey: ['wishlists', 'mine'],
    queryFn: () => wishlistApi.mine(),
    enabled: !!user,
  });

  useEffect(() => {
    if (!selectedWishlistId && wishlistsQuery.data && wishlistsQuery.data.length > 0) {
      setSelectedWishlistId(wishlistsQuery.data[0].id);
    }
  }, [wishlistsQuery.data, selectedWishlistId]);

  const detailQuery = useQuery({
    queryKey: ['wishlists', selectedWishlistId],
    queryFn: () => wishlistApi.detail(selectedWishlistId as string),
    enabled: !!selectedWishlistId,
  });

  const createWishlistMutation = useMutation({
    mutationFn: (payload: WishlistFormValues) => wishlistApi.create(payload),
    onSuccess: (wishlist) => {
      toast.success('Список создан');
      wishlistForm.reset();
      queryClient.invalidateQueries({ queryKey: ['wishlists', 'mine'] });
      setSelectedWishlistId(wishlist.id);
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Не удалось создать список');
    },
  });

  const publishMutation = useMutation({
    mutationFn: (wishlistId: string) => wishlistApi.publish(wishlistId),
    onSuccess: () => {
      toast.success('Список опубликован');
      queryClient.invalidateQueries({ queryKey: ['wishlists', selectedWishlistId] });
      queryClient.invalidateQueries({ queryKey: ['wishlists', 'mine'] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : 'Ошибка публикации'),
  });

  const closeMutation = useMutation({
    mutationFn: (wishlistId: string) => wishlistApi.close(wishlistId),
    onSuccess: () => {
      toast.success('Список закрыт');
      queryClient.invalidateQueries({ queryKey: ['wishlists', selectedWishlistId] });
      queryClient.invalidateQueries({ queryKey: ['wishlists', 'mine'] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : 'Ошибка закрытия'),
  });

  const createItemMutation = useMutation({
    mutationFn: ({ wishlistId, payload }: { wishlistId: string; payload: ItemFormValues }) =>
      wishlistApi.createItem(wishlistId, {
        title: payload.title,
        product_url: payload.product_url || undefined,
        image_url: payload.image_url || undefined,
        notes: payload.notes || undefined,
        price: payload.price || undefined,
        mode: payload.mode,
        target_amount: payload.mode === 'group' ? payload.target_amount || payload.price || undefined : undefined,
      }),
    onSuccess: () => {
      toast.success('Подарок добавлен');
      itemForm.reset({
        title: '',
        product_url: '',
        image_url: '',
        notes: '',
        price: '',
        mode: 'single',
        target_amount: '',
      });
      queryClient.invalidateQueries({ queryKey: ['wishlists', selectedWishlistId] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : 'Ошибка добавления подарка'),
  });

  const archiveItemMutation = useMutation({
    mutationFn: ({ wishlistId, itemId }: { wishlistId: string; itemId: string }) =>
      wishlistApi.archiveItem(wishlistId, itemId),
    onSuccess: () => {
      toast.success('Подарок архивирован');
      queryClient.invalidateQueries({ queryKey: ['wishlists', selectedWishlistId] });
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : 'Ошибка архивации'),
  });

  const selectedWishlist = detailQuery.data;

  const publicLink = useMemo(() => {
    if (!selectedWishlist?.share_slug) return null;
    if (typeof window === 'undefined') return `/wishlist/${selectedWishlist.share_slug}`;
    return `${window.location.origin}/wishlist/${selectedWishlist.share_slug}`;
  }, [selectedWishlist?.share_slug]);

  const handlePreviewFromLink = async () => {
    const url = itemForm.getValues('product_url');
    if (!url) {
      toast.error('Сначала вставь ссылку');
      return;
    }
    try {
      const preview = await utilityApi.preview(url);
      if (preview.title) itemForm.setValue('title', preview.title);
      if (preview.image_url) itemForm.setValue('image_url', preview.image_url);
      if (preview.price) itemForm.setValue('price', preview.price);
      toast.success(preview.from_cache ? 'Данные загружены из кэша' : 'Данные подтянуты по ссылке');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Не удалось автозаполнить');
    }
  };

  if (loading) {
    return <div className='mx-auto max-w-6xl px-4 py-8 text-slate-600'>Загрузка...</div>;
  }

  if (!user) {
    return (
      <div className='mx-auto max-w-6xl px-4 py-8'>
        <Card>
          <CardContent className='py-8 text-center'>
            <p className='text-slate-700'>Чтобы управлять списками, войди в аккаунт.</p>
            <div className='mt-4'>
              <a href='/auth/login' className='text-violet-600 hover:underline'>
                Перейти ко входу
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className='mx-auto grid w-full max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[320px,1fr]'>
      <div className='space-y-6'>
        <Card>
          <CardHeader>
            <CardTitle>Новый вишлист</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className='space-y-3'
              onSubmit={wishlistForm.handleSubmit((values) => createWishlistMutation.mutate(values))}
            >
              <Input placeholder='Название' {...wishlistForm.register('title', { required: true })} />
              <Textarea placeholder='Описание' rows={3} {...wishlistForm.register('description')} />
              <Input placeholder='Повод (ДР, Новый год...)' {...wishlistForm.register('occasion')} />
              <Input type='date' {...wishlistForm.register('event_date')} />
              <Button type='submit' className='w-full' disabled={createWishlistMutation.isPending}>
                Создать список
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Мои списки</CardTitle>
          </CardHeader>
          <CardContent className='space-y-2'>
            {wishlistsQuery.data?.length ? (
              wishlistsQuery.data.map((wishlist) => (
                <button
                  key={wishlist.id}
                  onClick={() => setSelectedWishlistId(wishlist.id)}
                  className={`w-full rounded-xl border px-3 py-2 text-left transition ${
                    selectedWishlistId === wishlist.id
                      ? 'border-violet-500 bg-violet-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <p className='font-medium text-slate-900'>{wishlist.title}</p>
                  <p className='text-xs text-slate-500'>{wishlist.status}</p>
                </button>
              ))
            ) : (
              <p className='text-sm text-slate-500'>Пока нет списков</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className='space-y-6'>
        {selectedWishlist ? (
          <>
            <Card>
              <CardHeader>
                <CardTitle>{selectedWishlist.title}</CardTitle>
                <p className='text-sm text-slate-600'>{selectedWishlist.description || 'Без описания'}</p>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div className='flex flex-wrap gap-2'>
                  {selectedWishlist.status !== 'published' && (
                    <Button
                      onClick={() => publishMutation.mutate(selectedWishlist.id)}
                      disabled={publishMutation.isPending}
                    >
                      Опубликовать
                    </Button>
                  )}
                  {selectedWishlist.status !== 'closed' && (
                    <Button
                      variant='ghost'
                      onClick={() => closeMutation.mutate(selectedWishlist.id)}
                      disabled={closeMutation.isPending}
                    >
                      Закрыть
                    </Button>
                  )}
                </div>

                {publicLink && (
                  <div className='rounded-xl border border-slate-200 bg-slate-50 p-3'>
                    <p className='text-xs uppercase tracking-wide text-slate-500'>Публичная ссылка</p>
                    <div className='mt-2 flex items-center gap-2'>
                      <a href={publicLink} className='truncate text-sm text-violet-600 hover:underline'>
                        {publicLink}
                      </a>
                      <Button
                        variant='ghost'
                        onClick={async () => {
                          await navigator.clipboard.writeText(publicLink);
                          toast.success('Ссылка скопирована');
                        }}
                      >
                        <Copy className='h-4 w-4' />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Добавить подарок</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  className='space-y-3'
                  onSubmit={itemForm.handleSubmit((values) => {
                    if (!selectedWishlistId) return;
                    createItemMutation.mutate({ wishlistId: selectedWishlistId, payload: values });
                  })}
                >
                  <Input placeholder='Название подарка' {...itemForm.register('title', { required: true })} />

                  <div className='flex gap-2'>
                    <Input
                      placeholder='https://example.com/product'
                      {...itemForm.register('product_url')}
                    />
                    <Button type='button' variant='ghost' onClick={handlePreviewFromLink}>
                      <Sparkles className='h-4 w-4' />
                    </Button>
                  </div>

                  <Input placeholder='Ссылка на изображение' {...itemForm.register('image_url')} />
                  <Textarea placeholder='Комментарий' rows={2} {...itemForm.register('notes')} />

                  <div className='grid gap-2 sm:grid-cols-3'>
                    <Input placeholder='Цена' {...itemForm.register('price')} />
                    <select
                      className='rounded-xl border border-slate-300 px-3 py-2 text-sm'
                      {...itemForm.register('mode')}
                    >
                      <option value='single'>Один даритель</option>
                      <option value='group'>Сбор с друзей</option>
                    </select>
                    <Input placeholder='Цель сбора' {...itemForm.register('target_amount')} />
                  </div>

                  <Button type='submit' disabled={createItemMutation.isPending}>
                    Добавить
                  </Button>
                </form>
              </CardContent>
            </Card>

            <div className='grid gap-4'>
              {selectedWishlist.items.map((item) => (
                <WishlistItemCard
                  key={item.id}
                  item={item}
                  currency={selectedWishlist.currency}
                  ownerView
                  onArchive={(itemId) => {
                    if (!selectedWishlistId) return;
                    archiveItemMutation.mutate({ wishlistId: selectedWishlistId, itemId });
                  }}
                  loading={archiveItemMutation.isPending}
                />
              ))}
            </div>
          </>
        ) : (
          <Card>
            <CardContent className='py-10 text-center text-slate-600'>
              Выбери список слева или создай новый.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
