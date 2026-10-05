// Где подают документы — «канал подачи» вуза. Чистая логика выбора, без
// обращения к базе и без импортов: модуль читается и тестами (vitest не
// понимает алиас "@/").
//
// Запись хранится на вуз и уровень (supabase/migrations/
// 20261005120000_application_channel.sql), а не на программу: куда подавать,
// зависит от вуза и уровня. Показываются только строки, подтверждённые
// человеком (правило 6 CLAUDE.md) — неподтверждённых этот код не видит
// вовсе, их отсекает политика доступа в базе.

// unified_portal — единая подача через государственный портал услуг;
// university — подача в сам вуз (его система, почта или лично): порядок
// описан на странице вуза, куда ведёт ссылка.
export const CHANNEL_TYPES = ["unified_portal", "university"] as const;
export type ChannelType = (typeof CHANNEL_TYPES)[number];

export type ApplicationChannel = {
  universityId: string;
  /** null — запись действует для всех уровней вуза. */
  degreeLevel: string | null;
  channelType: ChannelType;
  /** Куда вести человека: услуга на портале либо страница вуза о подаче. */
  url: string;
  sourceUrl: string;
  verifiedAt: string;
};

// Запись с уровнем программы важнее записи «все уровни»: у вуза бакалавриат
// может идти через единую подачу, а всё остальное — через собственную систему.
export function matchChannel(
  channels: ApplicationChannel[],
  universityId: string,
  degreeLevel: string,
): ApplicationChannel | null {
  const own = channels.filter((channel) => channel.universityId === universityId);
  return (
    own.find((channel) => channel.degreeLevel === degreeLevel) ??
    own.find((channel) => channel.degreeLevel === null) ??
    null
  );
}

// Ссылка попадает в href. Значение подтверждает человек, но схему всё равно
// проверяем: «javascript:…» в базе не должен стать исполняемой ссылкой.
export function httpUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : null;
  } catch {
    return null;
  }
}
