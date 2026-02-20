'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Shield } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/auth-provider';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { authApi } from '@/lib/api';

interface LoginValues {
  email: string;
  password: string;
}

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const form = useForm<LoginValues>({
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (values: LoginValues) => {
    try {
      await login(values);
      toast.success('С возвращением!');
      router.push('/dashboard');
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Не удалось войти');
    }
  };

  return (
    <div className='mx-auto flex min-h-[calc(100vh-80px)] max-w-md items-center px-4 py-8'>
      <Card className='w-full animate-enter'>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Shield className='h-5 w-5 text-brand-300' />
            Вход в WishWave
          </CardTitle>
          <p className='text-sm text-slate-300'>
            Best-effort защита от агрессивной автоподстановки браузера уже включена.
          </p>
        </CardHeader>

        <CardContent>
          <form
            className='space-y-3'
            autoComplete='off'
            onSubmit={form.handleSubmit(onSubmit)}
            aria-label='Форма входа'
          >
            <input
              type='text'
              name='fake_username'
              autoComplete='username'
              tabIndex={-1}
              className='absolute -left-[9999px] top-auto h-0 w-0 opacity-0'
              aria-hidden
            />
            <input
              type='password'
              name='fake_password'
              autoComplete='current-password'
              tabIndex={-1}
              className='absolute -left-[9999px] top-auto h-0 w-0 opacity-0'
              aria-hidden
            />

            <label className='space-y-1.5'>
              <span className='text-xs font-medium uppercase tracking-wide text-slate-400'>Email</span>
              <Input
                placeholder='you@example.com'
                type='email'
                autoComplete='username'
                autoCapitalize='none'
                autoCorrect='off'
                spellCheck={false}
                inputMode='email'
                aria-label='Email'
                {...form.register('email', { required: true })}
              />
            </label>

            <label className='space-y-1.5'>
              <span className='text-xs font-medium uppercase tracking-wide text-slate-400'>Пароль</span>
              <Input
                placeholder='••••••••'
                type='password'
                autoComplete='current-password'
                aria-label='Пароль'
                {...form.register('password', { required: true })}
              />
            </label>

            <Button className='w-full' type='submit'>
              Войти
            </Button>
          </form>

          <Button
            variant='secondary'
            className='mt-3 w-full'
            onClick={() => {
              window.location.href = authApi.googleStartUrl();
            }}
          >
            <Mail className='h-4 w-4' />
            Войти через Google
          </Button>

          <p className='mt-4 text-center text-sm text-slate-300'>
            Нет аккаунта?{' '}
            <Link href='/auth/register' className='font-medium text-cyan-300 hover:text-cyan-200'>
              Зарегистрироваться
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
