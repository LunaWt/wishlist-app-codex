import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import { AppHeader } from '@/components/layout/app-header';
import { AppProviders } from '@/components/providers/app-providers';

import './globals.css';

const inter = Inter({ subsets: ['latin', 'cyrillic'] });

export const metadata: Metadata = {
  title: 'WishWave | Social Wishlist',
  description: 'Create wishlists, share links, reserve gifts and fund together in realtime.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang='ru'>
      <body className={`${inter.className} bg-slate-50 text-slate-900 antialiased`}>
        <AppProviders>
          <AppHeader />
          {children}
        </AppProviders>
      </body>
    </html>
  );
}
