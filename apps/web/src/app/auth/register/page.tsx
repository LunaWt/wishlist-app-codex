'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Sparkles } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';

import { useAuth } from '@/components/providers/auth-provider';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

interface RegisterValues {
  display_name: string;
  email: string;
  password: string;
}

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const form = useForm<RegisterValues>({
    defaultValues: {
      display_name: '',
      email: '',
      password: '',
    },
  });

  const onSubmit = async (values: RegisterValues) => {
    try {
      await register(values);
      toast.success('Аккаунт создан');
      router.push('/dashboard');
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Не удалось зарегистрироваться');
    }
  };

  return (
    <div className='mx-auto flex min-h-[calc(100vh-80px)] max-w-md items-center px-4 py-8'>
      <Card className='w-full animate-enter'>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <Sparkles className='h-5 w-5 text-cyan-300' />
            Регистрация
          </CardTitle>
          <p className='text-sm text-slate-300'>Создай аккаунт и начни собирать вишлисты уже сегодня.</p>
        </CardHeader>

        <CardContent>
          <form
            className='space-y-3'
            autoComplete='off'
            onSubmit={form.handleSubmit(onSubmit)}
            aria-label='Форма регистрации'
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
              autoComplete='new-password'
              tabIndex={-1}
              className='absolute -left-[9999px] top-auto h-0 w-0 opacity-0'
              aria-hidden
            />

            <label className='space-y-1.5'>
              <span className='text-xs font-medium uppercase tracking-wide text-slate-400'>Имя</span>
              <Input
                placeholder='Как тебя назвать?'
                autoComplete='name'
                aria-label='Имя'
                {...form.register('display_name', { required: true })}
              />
            </label>

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
                placeholder='Минимум 8 символов'
                type='password'
                autoComplete='new-password'
                aria-label='Пароль'
                {...form.register('password', { required: true })}
              />
            </label>

            <Button className='w-full' type='submit'>
              Создать аккаунт
            </Button>
          </form>

          <p className='mt-4 text-center text-sm text-slate-300'>
            Уже есть аккаунт?{' '}
            <Link href='/auth/login' className='font-medium text-cyan-300 hover:text-cyan-200'>
              Войти
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
