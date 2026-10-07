import { useSyncExternalStore } from 'react';
import { asset } from '../lib/content';
import { useI18n } from '../i18n/useI18n';

/** Temperatura que muestra la LCD real de la foto del dispositivo. */
const DEVICE_TEMP = 163.2;
const DEVICE_SET = 180;

function subscribeMotion(onChange: () => void) {
  const query = window.matchMedia('(prefers-reduced-motion: reduce)');
  query.addEventListener('change', onChange);
  return () => query.removeEventListener('change', onChange);
}

function useReducedMotion() {
  return useSyncExternalStore(
    subscribeMotion,
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    () => false,
  );
}

export function HeroScene() {
  const { t } = useI18n();
  const reduced = useReducedMotion();
  const heat = 0.72;

  return (
    <div className="relative mx-auto w-full max-w-[680px]">
      <div className="relative aspect-[5/4] sm:aspect-[6/5]">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-[42%] top-[40%] z-[1] h-24 w-24 rounded-full bg-accent/45 blur-3xl sm:h-32 sm:w-32"
          style={{ opacity: 0.2 + heat * 0.55 }}
        />

        <div className={`absolute right-[2%] top-[4%] z-0 w-[70%] sm:right-0 sm:w-[72%] ${reduced ? '' : 'hero-sway-studio'}`}>
          <div className="overflow-hidden rounded-xl border border-white/50 bg-white shadow-[0_28px_56px_-22px_rgba(0,0,0,0.7)] ring-1 ring-black/10">
            <div className="flex h-8 items-center gap-1.5 border-b border-black/5 bg-[#f3f1ef] px-3" aria-hidden="true">
              <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
              <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
              <span className="ml-2 truncate font-mono text-[10px] text-black/45">{t('hero.studio')}</span>
            </div>
            <div className="relative">
              <img
                src={asset('media/studio-heat-hero.png')}
                alt=""
                width={1280}
                height={1141}
                className="block h-auto w-full"
              />
              <div className="absolute left-[1.6%] top-[14.5%] w-[23.5%] rounded-md bg-white/92 px-2 py-1.5 shadow-sm ring-1 ring-black/5 backdrop-blur-[2px] sm:px-2.5 sm:py-2">
                <p className="text-[8px] font-semibold uppercase tracking-[0.12em] text-[#6b5a51] sm:text-[9px]">{t('hero.measured')}</p>
                <p className="font-display text-[18px] font-semibold leading-none text-accent tabular-nums sm:text-[22px]">
                  {DEVICE_TEMP.toFixed(1)}
                  <span className="ml-0.5 text-[0.45em]">°C</span>
                </p>
                <p className="mt-1 truncate text-[8px] font-medium text-[#6b5a51] sm:text-[9px]">
                  {t('hero.phase.ramp', { n: '2' })} · {t('hero.setpoint')} {DEVICE_SET} °C
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className={`absolute bottom-0 left-0 z-10 w-[88%] sm:left-[-2%] sm:w-[90%] ${reduced ? '' : 'hero-sway-device'}`}>
          <div className="relative">
            <img
              src={asset('media/hero-device.png')}
              alt={t('hero.deviceAlt')}
              width={833}
              height={546}
              className="block h-auto w-full"
              style={{
                filter: `drop-shadow(0 0 1px rgba(251,245,239,0.4)) drop-shadow(0 20px 28px rgba(0,0,0,0.55)) drop-shadow(0 0 ${10 + heat * 16}px rgba(255,107,61,${0.12 + heat * 0.4}))`,
              }}
            />
            <div
              aria-hidden="true"
              className="pointer-events-none absolute left-[14%] top-[4%] h-[24%] w-[68%] rounded-[50%] mix-blend-screen"
              style={{
                background: 'radial-gradient(ellipse at center, rgba(255,120,60,0.8), transparent 70%)',
                opacity: 0.08 + heat * 0.55,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
