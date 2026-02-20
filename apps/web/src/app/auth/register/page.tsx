'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
  const form = useForm<RegisterValues>();

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
    <div className='mx-auto flex min-h-[calc(100vh-80px)] max-w-md items-center px-4'>
      <Card className='w-full'>
        <CardHeader>
          <CardTitle>Регистрация</CardTitle>
        </CardHeader>
        <CardContent>
          <form className='space-y-3' onSubmit={form.handleSubmit(onSubmit)}>
            <Input placeholder='Имя' {...form.register('display_name', { required: true })} />
            <Input placeholder='Email' type='email' {...form.register('email', { required: true })} />
            <Input placeholder='Пароль (минимум 8 символов)' type='password' {...form.register('password', { required: true })} />
            <Button className='w-full' type='submit'>
              Создать аккаунт
            </Button>
          </form>

          <p className='mt-4 text-center text-sm text-slate-600'>
            Уже есть аккаунт?{' '}
            <Link href='/auth/login' className='text-violet-600 hover:underline'>
              Войти
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
