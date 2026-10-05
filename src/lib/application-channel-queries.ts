import { cache } from "react";
import { supabase } from "@/lib/supabase";
import { CHANNEL_TYPES, type ApplicationChannel, type ChannelType } from "@/lib/application-channel";

// Каналы подачи одного вуза — только подтверждённые. Гейт на verified_at
// стоит и здесь, и в политике доступа application_channel_public_read
// (она и есть настоящая граница: anon-ключ публичный). Запрос узкий — по
// одному вузу: карточке программы другие не нужны.
export const getApplicationChannels = cache(async (universityId: string): Promise<ApplicationChannel[]> => {
  const { data, error } = await supabase
    .from("application_channel")
    .select("university_id, degree_level, channel_type, url, source_url, verified_at")
    .eq("university_id", universityId)
    .not("verified_at", "is", null);

  // Ошибка здесь не роняет карточку программы: блок «где подать» —
  // дополнение, без него страница полноценна. В частности, так страница
  // переживает промежуток между выкладкой кода и применением миграции
  // (таблицы ещё нет — PostgREST отвечает ошибкой).
  if (error) return [];

  return (data ?? [])
    .filter((row) => (CHANNEL_TYPES as readonly string[]).includes(row.channel_type))
    .map((row) => ({
      universityId: row.university_id,
      degreeLevel: row.degree_level,
      channelType: row.channel_type as ChannelType,
      url: row.url,
      sourceUrl: row.source_url,
      verifiedAt: row.verified_at,
    }));
});
