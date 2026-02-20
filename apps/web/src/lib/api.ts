import {
  AuthResponse,
  ContributionResponse,
  EventsResponse,
  GuestSessionResponse,
  ItemPreviewResponse,
  OwnerWishlistDetail,
  PublicWishlistView,
  WishlistSummary,
} from '@/lib/contracts';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: 'include',
    cache: 'no-store',
  });

  if (!response.ok) {
    let message = 'Request failed';
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // ignore parsing errors
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}

export { ApiError, API_BASE };

export const authApi = {
  register(payload: { email: string; password: string; display_name: string }) {
    return apiFetch<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  login(payload: { email: string; password: string }) {
    return apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  logout() {
    return apiFetch<{ message: string }>('/auth/logout', { method: 'POST' });
  },
  me() {
    return apiFetch<AuthResponse>('/auth/me');
  },
  googleStartUrl() {
    return `${API_BASE}/auth/google/start`;
  },
};

export const wishlistApi = {
  create(payload: {
    title: string;
    description?: string;
    occasion?: string;
    currency?: string;
    event_date?: string;
  }) {
    return apiFetch<OwnerWishlistDetail>('/wishlists', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  mine() {
    return apiFetch<WishlistSummary[]>('/wishlists/mine');
  },
  detail(id: string) {
    return apiFetch<OwnerWishlistDetail>(`/wishlists/${id}`);
  },
  update(id: string, payload: Record<string, unknown>) {
    return apiFetch<OwnerWishlistDetail>(`/wishlists/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },
  publish(id: string) {
    return apiFetch<OwnerWishlistDetail>(`/wishlists/${id}/publish`, { method: 'POST' });
  },
  close(id: string) {
    return apiFetch<OwnerWishlistDetail>(`/wishlists/${id}/close`, { method: 'POST' });
  },
  createItem(
    wishlistId: string,
    payload: {
      title: string;
      product_url?: string;
      image_url?: string;
      notes?: string;
      price?: string;
      mode: 'single' | 'group';
      target_amount?: string;
    },
  ) {
    return apiFetch<OwnerWishlistDetail>(`/wishlists/${wishlistId}/items`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  updateItem(
    wishlistId: string,
    itemId: string,
    payload: Record<string, unknown>,
  ) {
    return apiFetch<OwnerWishlistDetail>(`/wishlists/${wishlistId}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },
  archiveItem(wishlistId: string, itemId: string) {
    return apiFetch<OwnerWishlistDetail>(`/wishlists/${wishlistId}/items/${itemId}/archive`, {
      method: 'POST',
    });
  },
};

function guestHeaders(guestToken?: string): HeadersInit | undefined {
  if (!guestToken) return undefined;
  return { 'X-Guest-Token': guestToken };
}

export const publicApi = {
  getWishlist(shareSlug: string, guestToken?: string) {
    return apiFetch<PublicWishlistView>(`/public/w/${shareSlug}`, {
      headers: guestHeaders(guestToken),
    });
  },
  createGuestSession(shareSlug: string, payload: { name: string }) {
    return apiFetch<GuestSessionResponse>(`/public/w/${shareSlug}/guest-session`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  reserve(shareSlug: string, itemId: string, guestToken: string) {
    return apiFetch<{ message: string; item_id: string; is_reserved: boolean }>(
      `/public/w/${shareSlug}/items/${itemId}/reserve`,
      {
        method: 'POST',
        headers: guestHeaders(guestToken),
      },
    );
  },
  unreserve(shareSlug: string, itemId: string, guestToken: string) {
    return apiFetch<{ message: string; item_id: string; is_reserved: boolean }>(
      `/public/w/${shareSlug}/items/${itemId}/reserve`,
      {
        method: 'DELETE',
        headers: guestHeaders(guestToken),
      },
    );
  },
  contribute(shareSlug: string, itemId: string, guestToken: string, amount: string) {
    return apiFetch<ContributionResponse>(`/public/w/${shareSlug}/items/${itemId}/contributions`, {
      method: 'POST',
      headers: guestHeaders(guestToken),
      body: JSON.stringify({ amount }),
    });
  },
  events(shareSlug: string, cursor?: number) {
    const query = cursor ? `?cursor=${cursor}` : '';
    return apiFetch<EventsResponse>(`/public/w/${shareSlug}/events${query}`);
  },
};

export const utilityApi = {
  preview(url: string) {
    return apiFetch<ItemPreviewResponse>('/items/preview', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  },
};
