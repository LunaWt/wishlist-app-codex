'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
  const form = useForm<LoginValues>();

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
    <div className='mx-auto flex min-h-[calc(100vh-80px)] max-w-md items-center px-4'>
      <Card className='w-full'>
        <CardHeader>
          <CardTitle>Вход</CardTitle>
        </CardHeader>
        <CardContent>
          <form className='space-y-3' onSubmit={form.handleSubmit(onSubmit)}>
            <Input placeholder='Email' type='email' {...form.register('email', { required: true })} />
            <Input placeholder='Пароль' type='password' {...form.register('password', { required: true })} />
            <Button className='w-full' type='submit'>
              Войти
            </Button>
          </form>

          <Button
            variant='ghost'
            className='mt-3 w-full'
            onClick={() => {
              window.location.href = authApi.googleStartUrl();
            }}
          >
            Войти через Google
          </Button>

          <p className='mt-4 text-center text-sm text-slate-600'>
            Нет аккаунта?{' '}
            <Link href='/auth/register' className='text-violet-600 hover:underline'>
              Зарегистрироваться
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
