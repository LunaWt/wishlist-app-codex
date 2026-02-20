const prefix = 'wishlist_guest_token:';

export function getGuestToken(slug: string) {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(`${prefix}${slug}`);
}

export function setGuestToken(slug: string, token: string) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(`${prefix}${slug}`, token);
}
