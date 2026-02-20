'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Copy, ExternalLink, Loader2, Sparkles, Wand2 } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/auth-provider';
import { WishlistItemCard } from '@/components/wishlist/wishlist-item-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { utilityApi, wishlistApi } from '@/lib/api';
import { ItemPreviewResponse } from '@/lib/contracts';
import { formatMoney } from '@/lib/utils';

interface WishlistFormValues {
  title: string;
  description: string;
  currency: string;
}

interface ItemFormValues {
  product_url: string;
  title: string;
  notes: string;
  mode: 'single' | 'group';
  target_amount: string;
  price: string;
  image_url: string;
}

type PreviewState = {
  status: 'idle' | 'loading' | 'success' | 'partial' | 'error';
  message: string;
};

function isHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:';
  } catch {
    return false;
  }
}

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const { user, loading } = useAuth();

  const [selectedWishlistId, setSelectedWishlistId] = useState<string | null>(null);
  const [previewState, setPreviewState] = useState<PreviewState>({ status: 'idle', message: '' });
  const lastPreviewUrlRef = useRef<string | null>(null);

  const wishlistForm = useForm<WishlistFormValues>({
    defaultValues: {
      title: '',
      description: '',
      currency: 'RUB',
    },
  });

  const itemForm = useForm<ItemFormValues>({
    defaultValues: {
      product_url: '',
      title: '',
      notes: '',
      mode: 'single',
      target_amount: '',
      price: '',
      image_url: '',
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
      wishlistForm.reset({ title: '', description: '', currency: wishlist.currency || 'RUB' });
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
        target_amount:
          payload.mode === 'group' ? payload.target_amount || payload.price || undefined : undefined,
      }),
    onSuccess: () => {
      toast.success('Подарок добавлен');
      itemForm.reset({
        product_url: '',
        title: '',
        notes: '',
        mode: 'single',
        target_amount: '',
        price: '',
        image_url: '',
      });
      setPreviewState({ status: 'idle', message: '' });
      lastPreviewUrlRef.current = null;
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
  const productUrl = useWatch({ control: itemForm.control, name: 'product_url' }) ?? '';
  const watchedTitle = useWatch({ control: itemForm.control, name: 'title' }) ?? '';
  const watchedImageUrl = useWatch({ control: itemForm.control, name: 'image_url' }) ?? '';
  const watchedPrice = useWatch({ control: itemForm.control, name: 'price' }) ?? '';
  const productUrlRegister = itemForm.register('product_url', { required: true });

  const publicLink = useMemo(() => {
    if (!selectedWishlist?.share_slug) return null;
    if (typeof window === 'undefined') return `/wishlist/${selectedWishlist.share_slug}`;
    return `${window.location.origin}/wishlist/${selectedWishlist.share_slug}`;
  }, [selectedWishlist?.share_slug]);

  const applyPreviewToForm = useCallback((preview: ItemPreviewResponse, force: boolean) => {
    const currentTitle = itemForm.getValues('title').trim();
    const currentPrice = itemForm.getValues('price').trim();
    const currentImage = itemForm.getValues('image_url').trim();

    if (preview.title && (force || !currentTitle || !itemForm.getFieldState('title').isDirty)) {
      itemForm.setValue('title', preview.title, { shouldDirty: false });
    }

    if (preview.price && (force || !currentPrice || !itemForm.getFieldState('price').isDirty)) {
      itemForm.setValue('price', preview.price, { shouldDirty: false });
    }

    if (preview.image_url && (force || !currentImage || !itemForm.getFieldState('image_url').isDirty)) {
      itemForm.setValue('image_url', preview.image_url, { shouldDirty: false });
    }
  }, [itemForm]);

  const fetchPreview = useCallback(async (options?: { force?: boolean }) => {
    const force = options?.force ?? false;
    const url = itemForm.getValues('product_url').trim();

    if (!url) {
      setPreviewState({ status: 'idle', message: '' });
      return;
    }

    if (!isHttpUrl(url)) {
      setPreviewState({ status: 'error', message: 'Ссылка должна начинаться с http:// или https://' });
      return;
    }

    if (!force && lastPreviewUrlRef.current === url) {
      return;
    }

    setPreviewState({ status: 'loading', message: 'Подтягиваем данные с карточки товара…' });

    try {
      const preview = await utilityApi.preview(url);
      applyPreviewToForm(preview, force);
      lastPreviewUrlRef.current = url;

      const hasTitle = Boolean(preview.title);
      const hasImage = Boolean(preview.image_url);
      const hasPrice = Boolean(preview.price);

      if (hasTitle && hasImage && hasPrice) {
        setPreviewState({
          status: 'success',
          message: preview.from_cache
            ? 'Данные загружены из кэша. Можно сразу добавлять товар.'
            : 'Готово! Название, изображение и цена подставлены.',
        });
      } else if (hasTitle || hasImage || hasPrice) {
        setPreviewState({
          status: 'partial',
          message: 'Часть данных найдена. Остальное можно заполнить вручную.',
        });
      } else {
        setPreviewState({
          status: 'partial',
          message: 'Метаданные не найдены. Заполни поля вручную — это нормально.',
        });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось получить данные по ссылке';
      setPreviewState({
        status: 'error',
        message: `${message}. Заполни товар вручную и продолжай.`,
      });
      toast.error(message);
    }
  }, [applyPreviewToForm, itemForm]);

  useEffect(() => {
    const url = productUrl.trim();
    if (!isHttpUrl(url)) {
      return;
    }

    const timer = window.setTimeout(() => {
      void fetchPreview();
    }, 900);

    return () => window.clearTimeout(timer);
  }, [fetchPreview, productUrl]);

  if (loading) {
    return <div className='mx-auto max-w-6xl px-4 py-8 text-slate-300'>Загрузка...</div>;
  }

  if (!user) {
    return (
      <div className='mx-auto max-w-6xl px-4 py-8'>
        <Card className='animate-enter'>
          <CardContent className='py-10 text-center'>
            <p className='text-slate-200'>Чтобы управлять списками, войди в аккаунт.</p>
            <div className='mt-4'>
              <a href='/auth/login' className='font-medium text-cyan-300 hover:text-cyan-200'>
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
        <Card className='animate-enter'>
          <CardHeader>
            <CardTitle>Новый вишлист</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className='space-y-3'
              onSubmit={wishlistForm.handleSubmit((values) => createWishlistMutation.mutate(values))}
            >
              <Input placeholder='Название списка' {...wishlistForm.register('title', { required: true })} />
              <Textarea placeholder='Короткое описание (необязательно)' rows={3} {...wishlistForm.register('description')} />

              <label className='space-y-1 text-xs text-slate-400'>
                Валюта
                <select
                  className='w-full rounded-2xl border border-white/15 bg-slate-950/55 px-3.5 py-2.5 text-sm text-slate-100 outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/25'
                  {...wishlistForm.register('currency')}
                >
                  <option value='RUB'>RUB ₽</option>
                  <option value='USD'>USD $</option>
                  <option value='EUR'>EUR €</option>
                </select>
              </label>

              <Button type='submit' className='w-full' disabled={createWishlistMutation.isPending}>
                {createWishlistMutation.isPending ? (
                  <>
                    <Loader2 className='h-4 w-4 animate-spin' />
                    Создаём...
                  </>
                ) : (
                  'Создать список'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className='animate-enter'>
          <CardHeader>
            <CardTitle>Мои списки</CardTitle>
          </CardHeader>
          <CardContent className='space-y-2'>
            {wishlistsQuery.data?.length ? (
              wishlistsQuery.data.map((wishlist) => (
                <button
                  key={wishlist.id}
                  onClick={() => setSelectedWishlistId(wishlist.id)}
                  className={`w-full rounded-2xl border px-3 py-2 text-left transition ${
                    selectedWishlistId === wishlist.id
                      ? 'border-brand-400/60 bg-brand-500/20 text-white'
                      : 'border-white/10 bg-white/5 text-slate-200 hover:border-white/20 hover:bg-white/10'
                  }`}
                >
                  <p className='font-medium'>{wishlist.title}</p>
                  <p className='mt-1 text-xs uppercase tracking-wide text-slate-300/90'>{wishlist.status}</p>
                </button>
              ))
            ) : (
              <p className='text-sm text-slate-300'>Пока нет списков</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className='space-y-6'>
        {selectedWishlist ? (
          <>
            <Card className='animate-enter'>
              <CardHeader>
                <CardTitle>{selectedWishlist.title}</CardTitle>
                <p className='text-sm text-slate-300'>{selectedWishlist.description || 'Без описания'}</p>
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
                  <div className='rounded-2xl border border-white/10 bg-white/5 p-3'>
                    <p className='text-xs uppercase tracking-wide text-slate-400'>Публичная ссылка</p>
                    <div className='mt-2 flex items-center gap-2'>
                      <a
                        href={publicLink}
                        target='_blank'
                        rel='noreferrer'
                        className='truncate text-sm text-cyan-300 hover:text-cyan-200'
                      >
                        {publicLink}
                      </a>
                      <Button
                        variant='ghost'
                        onClick={async () => {
                          await navigator.clipboard.writeText(publicLink);
                          toast.success('Ссылка скопирована');
                        }}
                        aria-label='Скопировать ссылку'
                      >
                        <Copy className='h-4 w-4' />
                      </Button>
                      <a href={publicLink} target='_blank' rel='noreferrer'>
                        <Button variant='ghost' aria-label='Открыть ссылку'>
                          <ExternalLink className='h-4 w-4' />
                        </Button>
                      </a>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className='animate-enter'>
              <CardHeader>
                <CardTitle>Добавить подарок</CardTitle>
                <p className='text-sm text-slate-300'>
                  Основные поля: ссылка, название и дополнительное описание. Остальные параметры — в настройках ниже.
                </p>
              </CardHeader>

              <CardContent>
                <form
                  className='space-y-4'
                  onSubmit={itemForm.handleSubmit((values) => {
                    if (!selectedWishlistId) return;
                    createItemMutation.mutate({ wishlistId: selectedWishlistId, payload: values });
                  })}
                >
                  <div className='grid gap-3 lg:grid-cols-3'>
                    <div className='space-y-2'>
                      <label className='text-xs font-medium uppercase tracking-wide text-slate-400'>Ссылка на товар</label>
                      <Input
                        placeholder='https://ozon.ru/... или https://wildberries.ru/...'
                        {...productUrlRegister}
                        onBlur={(event) => {
                          productUrlRegister.onBlur(event);
                          void fetchPreview({ force: false });
                        }}
                      />
                    </div>

                    <div className='space-y-2'>
                      <label className='text-xs font-medium uppercase tracking-wide text-slate-400'>Название</label>
                      <Input placeholder='Название подарка' {...itemForm.register('title', { required: true })} />
                    </div>

                    <div className='space-y-2'>
                      <label className='text-xs font-medium uppercase tracking-wide text-slate-400'>Доп. описание</label>
                      <Textarea placeholder='Комментарий к подарку' rows={1} {...itemForm.register('notes')} />
                    </div>
                  </div>

                  <div className='flex flex-wrap items-center gap-2'>
                    <Button type='button' variant='secondary' onClick={() => void fetchPreview({ force: true })}>
                      <Wand2 className='h-4 w-4' />
                      Обновить по ссылке
                    </Button>

                    {previewState.status === 'loading' && (
                      <span className='inline-flex items-center gap-1 text-sm text-cyan-200'>
                        <Loader2 className='h-3.5 w-3.5 animate-spin' />
                        {previewState.message}
                      </span>
                    )}

                    {(previewState.status === 'success' || previewState.status === 'partial') && (
                      <span className='inline-flex items-center gap-1 text-sm text-emerald-200'>
                        <CheckCircle2 className='h-3.5 w-3.5' />
                        {previewState.message}
                      </span>
                    )}

                    {previewState.status === 'error' && <span className='text-sm text-rose-200'>{previewState.message}</span>}
                  </div>

                  <details className='rounded-2xl border border-white/10 bg-white/5 p-4'>
                    <summary className='cursor-pointer text-sm font-semibold text-slate-100'>Дополнительные настройки</summary>

                    <div className='mt-4 grid gap-3 sm:grid-cols-3'>
                      <label className='space-y-1 text-xs text-slate-400'>
                        Режим подарка
                        <select
                          className='w-full rounded-2xl border border-white/15 bg-slate-950/55 px-3.5 py-2.5 text-sm text-slate-100 outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/25'
                          {...itemForm.register('mode')}
                        >
                          <option value='single'>Один даритель</option>
                          <option value='group'>Сбор с друзей</option>
                        </select>
                      </label>

                      <label className='space-y-1 text-xs text-slate-400'>
                        Цена
                        <Input placeholder='0' {...itemForm.register('price')} />
                      </label>

                      <label className='space-y-1 text-xs text-slate-400'>
                        Цель сбора
                        <Input placeholder='Только для group-режима' {...itemForm.register('target_amount')} />
                      </label>
                    </div>

                    <div className='mt-3 space-y-1 text-xs text-slate-400'>
                      <span>URL изображения (можно отредактировать вручную)</span>
                      <Input placeholder='https://...' {...itemForm.register('image_url')} />
                    </div>
                  </details>

                  {(watchedImageUrl || watchedPrice) && (
                    <div className='rounded-2xl border border-white/10 bg-white/5 p-3'>
                      <p className='mb-2 text-xs uppercase tracking-wide text-slate-400'>Превью товара</p>
                      <div className='flex items-center gap-3'>
                        {watchedImageUrl ? (
                          <img src={watchedImageUrl} alt='Превью товара' className='h-16 w-16 rounded-xl object-cover' />
                        ) : (
                          <div className='flex h-16 w-16 items-center justify-center rounded-xl border border-white/10 bg-slate-900/40'>
                            <Sparkles className='h-4 w-4 text-slate-400' />
                          </div>
                        )}

                        <div>
                          <p className='text-sm font-medium text-slate-100'>{watchedTitle || 'Новый подарок'}</p>
                          <p className='text-xs text-slate-300'>
                            {watchedPrice ? formatMoney(watchedPrice, selectedWishlist.currency) : 'Цена не указана'}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <Button type='submit' disabled={createItemMutation.isPending}>
                    {createItemMutation.isPending ? (
                      <>
                        <Loader2 className='h-4 w-4 animate-spin' />
                        Добавляем...
                      </>
                    ) : (
                      'Добавить подарок'
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <div className='grid gap-4'>
              {selectedWishlist.items.length > 0 ? (
                selectedWishlist.items.map((item) => (
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
                ))
              ) : (
                <Card className='animate-enter'>
                  <CardContent className='py-10 text-center text-slate-300'>
                    Пока нет подарков. Добавь первый товар выше.
                  </CardContent>
                </Card>
              )}
            </div>
          </>
        ) : (
          <Card className='animate-enter'>
            <CardContent className='py-10 text-center text-slate-300'>
              Выбери список слева или создай новый.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
