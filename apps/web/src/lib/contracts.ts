export type WishlistStatus = 'draft' | 'published' | 'closed';
export type ItemMode = 'single' | 'group';
export type ItemStatus = 'active' | 'archived' | 'unavailable';

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface AuthResponse {
  user: AuthUser;
}

export interface WishlistSummary {
  id: string;
  title: string;
  description: string | null;
  currency: string;
  status: WishlistStatus;
  share_slug: string | null;
  created_at: string;
  updated_at: string;
}

export interface OwnerItemView {
  id: string;
  title: string;
  product_url: string | null;
  image_url: string | null;
  notes: string | null;
  price: string | null;
  mode: ItemMode;
  target_amount: string | null;
  collected_amount: string;
  status: ItemStatus;
  position: number;
  is_reserved: boolean;
  progress_percent: number;
}

export interface GuestItemView {
  id: string;
  title: string;
  product_url: string | null;
  image_url: string | null;
  notes: string | null;
  price: string | null;
  mode: ItemMode;
  target_amount: string | null;
  collected_amount: string;
  status: ItemStatus;
  position: number;
  is_reserved: boolean;
  reserved_by_you: boolean;
  my_contribution: string;
  progress_percent: number;
}

export interface OwnerWishlistDetail extends WishlistSummary {
  items: OwnerItemView[];
}

export interface PublicWishlistView {
  id: string;
  title: string;
  description: string | null;
  currency: string;
  status: WishlistStatus;
  share_slug: string;
  viewer_kind: 'anonymous' | 'guest' | 'owner';
  items: OwnerItemView[] | GuestItemView[];
}

export interface GuestSessionResponse {
  token: string;
  guest_session_id: string;
  guest_name: string;
  expires_at: string;
}

export interface RealtimeEvent {
  id: number;
  event_type: string;
  item_id: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface EventsResponse {
  events: RealtimeEvent[];
  next_cursor: number | null;
}

export interface ContributionResponse {
  message: string;
  item_id: string;
  accepted_amount: string;
  collected_amount: string;
  progress_percent: number;
}

export interface ItemPreviewResponse {
  title: string | null;
  image_url: string | null;
  price: string | null;
  currency: string | null;
  source_url: string;
  from_cache: boolean;
}
