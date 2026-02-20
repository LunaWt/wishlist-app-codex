import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import DashboardPage from '@/app/dashboard/page';

const { previewMock, wishlistSummary, wishlistDetail } = vi.hoisted(() => {
  const summary = {
    id: 'wishlist-1',
    title: 'День рождения',
    description: 'Список подарков',
    currency: 'RUB',
    status: 'draft',
    share_slug: null,
    created_at: '2026-02-20T10:00:00Z',
    updated_at: '2026-02-20T10:00:00Z',
  };

  return {
    previewMock: vi.fn(),
    wishlistSummary: summary,
    wishlistDetail: {
      ...summary,
      items: [],
    },
  };
});

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
  }),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('@/components/providers/auth-provider', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      email: 'owner@example.com',
      display_name: 'Owner',
      created_at: '2026-02-20T10:00:00Z',
    },
    loading: false,
  }),
}));

vi.mock('@/lib/api', () => ({
  wishlistApi: {
    mine: vi.fn().mockResolvedValue([wishlistSummary]),
    detail: vi.fn().mockResolvedValue(wishlistDetail),
    create: vi.fn(),
    publish: vi.fn(),
    close: vi.fn(),
    createItem: vi.fn(),
    archiveItem: vi.fn(),
  },
  utilityApi: {
    preview: previewMock,
  },
}));

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
  useQuery: ({ queryKey }: { queryKey: unknown[] }) => {
    if (queryKey[0] === 'wishlists' && queryKey[1] === 'mine') {
      return { data: [wishlistSummary], isLoading: false, isError: false };
    }

    if (queryKey[0] === 'wishlists' && queryKey[1] === 'wishlist-1') {
      return { data: wishlistDetail, isLoading: false, isError: false };
    }

    return { data: undefined, isLoading: false, isError: false };
  },
  useMutation: () => ({
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

describe('dashboard item form', () => {
  it('shows required 3-column fields and keeps manual title on autofill', async () => {
    previewMock.mockResolvedValue({
      title: 'Авто-название',
      image_url: 'https://images.example/item.webp',
      price: '7990.00',
      currency: 'RUB',
      source_url: 'https://www.ozon.ru/product/demo',
      from_cache: false,
    });

    render(<DashboardPage />);

    await screen.findByPlaceholderText('https://ozon.ru/... или https://wildberries.ru/...');

    expect(screen.getByText('Ссылка на товар')).toBeInTheDocument();
    expect(screen.getByText('Название')).toBeInTheDocument();
    expect(screen.getByText('Доп. описание')).toBeInTheDocument();
    expect(screen.queryByText('Повод (ДР, Новый год...)')).not.toBeInTheDocument();

    const urlInput = screen.getByPlaceholderText('https://ozon.ru/... или https://wildberries.ru/...');
    const titleInput = screen.getByPlaceholderText('Название подарка') as HTMLInputElement;

    fireEvent.change(titleInput, { target: { value: 'Ручное название' } });
    fireEvent.change(urlInput, { target: { value: 'https://www.ozon.ru/product/demo' } });
    fireEvent.blur(urlInput);

    await waitFor(() => expect(previewMock).toHaveBeenCalled());
    expect(titleInput.value).toBe('Ручное название');
  });
});
