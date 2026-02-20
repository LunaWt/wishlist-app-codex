'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect } from 'react';
import { toast } from 'sonner';

function CallbackContent() {
  const params = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const status = params.get('status');
    if (status === 'success') {
      toast.success('Google-авторизация прошла успешно');
      router.replace('/dashboard');
      return;
    }

    toast.error('Не удалось авторизоваться через Google');
    router.replace('/auth/login');
  }, [params, router]);

  return <div className='mx-auto max-w-md px-4 py-16 text-center text-slate-300'>Подтверждаем вход…</div>;
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className='mx-auto max-w-md px-4 py-16 text-center text-slate-300'>Загрузка…</div>}>
      <CallbackContent />
    </Suspense>
  );
}
