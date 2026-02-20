import type { Metadata } from 'next';

import { AppHeader } from '@/components/layout/app-header';
import { AppProviders } from '@/components/providers/app-providers';

import './globals.css';

export const metadata: Metadata = {
  title: 'WishWave | Social Wishlist',
  description: 'Create wishlists, share links, reserve gifts and fund together in realtime.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang='ru'>
      <body className='min-h-screen text-slate-100 antialiased font-sans'>
        <AppProviders>
          <AppHeader />
          {children}
        </AppProviders>
      </body>
    </html>
  );
}
