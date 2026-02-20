'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { useAuth } from '@/components/providers/auth-provider';
import { cn } from '@/lib/utils';

const navLinks = [
  { href: '/', label: 'Главная' },
  { href: '/dashboard', label: 'Мои списки' },
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
    <header className='sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur'>
      <div className='mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3'>
        <Link href='/' className='text-lg font-bold text-slate-900'>
          ✨ WishWave
        </Link>

        <nav className='hidden items-center gap-6 md:flex'>
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'text-sm font-medium transition',
                pathname === link.href ? 'text-violet-600' : 'text-slate-600 hover:text-slate-900',
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
              <span className='hidden text-sm text-slate-600 sm:inline'>Привет, {user.display_name}</span>
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
