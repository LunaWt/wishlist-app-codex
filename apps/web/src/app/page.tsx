import Link from 'next/link';
import { Gift, Rocket, ShieldCheck, Sparkles, Users } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

const features = [
  {
    icon: Gift,
    title: 'Без дублей подарков',
    description: 'Друзья резервируют позиции и не пересекаются между собой.',
  },
  {
    icon: Users,
    title: 'Совместные сборы',
    description: 'Дорогие подарки собираются вкладами с живым прогресс-баром.',
  },
  {
    icon: ShieldCheck,
    title: 'Сюрприз сохраняется',
    description: 'Владелец видит только агрегаты, без персональных данных.',
  },
];

export default function HomePage() {
  return (
    <main className='mx-auto max-w-6xl space-y-12 px-4 py-10 sm:px-6 sm:py-14'>
      <section className='grid items-center gap-10 lg:grid-cols-[1.05fr,0.95fr]'>
        <div className='space-y-6 animate-enter'>
          <p className='inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200'>
            <Sparkles className='h-3.5 w-3.5' />
            Social wishlist platform
          </p>

          <h1 className='text-4xl font-bold leading-tight text-white sm:text-5xl'>
            Собирай подарки красиво,
            <span className='gradient-text'> быстро и без спойлеров</span>
          </h1>

          <p className='max-w-xl text-base text-slate-300 sm:text-lg'>
            Создай вишлист, поделись ссылкой и получай realtime-обновления: резервы, вклад друзей и прогресс по
            каждому подарку.
          </p>

          <div className='flex flex-wrap items-center gap-3'>
            <Link href='/auth/register'>
              <Button className='px-6'>Начать бесплатно</Button>
            </Link>
            <Link href='/dashboard'>
              <Button variant='secondary' className='px-6'>
                Открыть дашборд
              </Button>
            </Link>
          </div>
        </div>

        <Card className='animate-enter animate-float overflow-hidden'>
          <CardContent className='space-y-5 p-7'>
            <div className='inline-flex rounded-2xl border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-medium text-cyan-100'>
              <Rocket className='mr-1.5 h-3.5 w-3.5' />
              Готово к демо и продакшену
            </div>

            <div className='space-y-3'>
              <h2 className='text-2xl font-semibold text-white'>Что умеет WishWave</h2>
              <p className='text-sm text-slate-300'>
                Публичная ссылка без логина, гостевые сессии, автоподтяжка товара по URL и realtime для всех
                участников.
              </p>
            </div>

            <div className='grid gap-3'>
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className='rounded-2xl border border-white/10 bg-white/5 p-3.5 transition hover:border-white/20 hover:bg-white/10'
                >
                  <feature.icon className='mb-2 h-4 w-4 text-brand-300' />
                  <p className='text-sm font-semibold text-white'>{feature.title}</p>
                  <p className='mt-1 text-xs text-slate-300'>{feature.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
