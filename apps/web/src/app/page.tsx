import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function HomePage() {
  return (
    <main className='mx-auto max-w-6xl px-4 py-12'>
      <section className='grid items-center gap-8 lg:grid-cols-2'>
        <div className='space-y-6'>
          <p className='inline-flex rounded-full bg-violet-100 px-3 py-1 text-sm font-medium text-violet-700'>
            Социальный wishlist с realtime
          </p>
          <h1 className='text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl'>
            Собирай подарки без дублей и спойлеров 🎁
          </h1>
          <p className='max-w-xl text-lg text-slate-600'>
            Создай список желаний, поделись ссылкой с друзьями и следи за прогрессом сборов. Владелец видит
            только итоговые суммы — сюрприз остаётся сюрпризом.
          </p>
          <div className='flex flex-wrap gap-3'>
            <Link href='/auth/register'>
              <Button>Создать wishlist</Button>
            </Link>
            <Link href='/dashboard'>
              <Button variant='ghost'>Открыть дашборд</Button>
            </Link>
          </div>
        </div>

        <Card className='border-violet-200 bg-gradient-to-br from-white to-violet-50'>
          <CardContent className='space-y-3 p-6'>
            <h2 className='text-xl font-semibold text-slate-900'>Что внутри</h2>
            <ul className='space-y-2 text-sm text-slate-700'>
              <li>• Публичная ссылка без регистрации</li>
              <li>• Резервы подарков и сборы вскладчину</li>
              <li>• Realtime-обновления без перезагрузки</li>
              <li>• Автозаполнение товара по URL</li>
              <li>• Мобильный адаптив и чистый UI</li>
            </ul>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
