'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/auth-provider';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const navLinks = [
  { href: '/', label: 'Главная' },
  { href: '/dashboard', label: 'Дашборд' },
];

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, loading } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Вы вышли из аккаунта');
      router.push('/');
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Не удалось выйти');
    }
  };

  return (
    <header className='sticky top-0 z-30 border-b border-white/10 bg-slate-950/65 backdrop-blur-xl'>
      <div className='mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 sm:px-6'>
        <Link href='/' className='inline-flex items-center gap-2 text-lg font-bold text-white'>
          <span className='inline-block rounded-xl bg-gradient-to-br from-brand-500 to-cyan-400 px-2 py-1 text-sm'>
            ✨
          </span>
          <span className='gradient-text'>WishWave</span>
        </Link>

        <nav className='hidden items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-1 md:flex'>
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'rounded-xl px-3 py-1.5 text-sm font-medium transition',
                pathname === link.href
                  ? 'bg-white/15 text-white'
                  : 'text-slate-300 hover:bg-white/10 hover:text-white',
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className='flex items-center gap-2'>
          {!loading && !user && (
            <>
              <Link href='/auth/login'>
                <Button variant='ghost'>Вход</Button>
              </Link>
              <Link href='/auth/register'>
                <Button>Регистрация</Button>
              </Link>
            </>
          )}

          {!loading && user && (
            <>
              <span className='hidden text-sm text-slate-300 sm:inline'>Привет, {user.display_name}</span>
              <Button variant='ghost' onClick={handleLogout}>
                Выйти
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
