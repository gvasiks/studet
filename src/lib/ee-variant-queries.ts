import { supabase } from "@/lib/supabase";
import { listProgrammes } from "@/lib/catalog";
import { remember } from "@/lib/server-memo";
import { admissionYear, eeVariants, type EeAdmissionYear, type EeVariant } from "@/lib/ee-variants";

// Подписи версий одного учебного плана у эстонских программ (ee-variants.ts):
// id программы -> чем она отличается от двойника. Только у программ с
// двойником — около 160 строк. Из памяти сервера на пять минут, как
// остальные данные каталога (server-memo.ts). Объект общий для всех
// запросов — только читать.

// PostgREST отдаёт не больше тысячи строк за запрос.
const PAGE_ROWS = 1000;

async function specializations(): Promise<Map<string, string>> {
  const result = new Map<string, string>();
  for (let from = 0; ; from += PAGE_ROWS) {
    const { data, error } = await supabase
      .from("ee_programme_field")
      .select("programme_id, specialization")
      .not("specialization", "is", null)
      .order("programme_id")
      .range(from, from + PAGE_ROWS - 1);
    // 42703 — колонки ещё нет: миграция 20261123130000 не применена. Тогда
    // различаем только по конкурсу.
    if (error?.code === "42703") return result;
    if (error) throw error;
    for (const row of data) result.set(row.programme_id as string, row.specialization as string);
    if (data.length < PAGE_ROWS) break;
  }
  return result;
}

async function admissions(): Promise<Map<string, EeAdmissionYear>> {
  const result = new Map<string, EeAdmissionYear>();
  for (let from = 0; ; from += PAGE_ROWS) {
    const { data, error } = await supabase
      .from("ee_admission")
      .select("programme_id, opens_at, closes_at")
      .order("programme_id")
      .range(from, from + PAGE_ROWS - 1);
    if (error) throw error;
    for (const row of data) {
      result.set(row.programme_id as string, { year: admissionYear(row.opens_at as string | null, row.closes_at as string | null) });
    }
    if (data.length < PAGE_ROWS) break;
  }
  return result;
}

export function getEeVariants(): Promise<Record<string, EeVariant>> {
  return remember("ee-variants", 5 * 60 * 1000, async () => {
    const [programmes, specs, rounds] = await Promise.all([listProgrammes("EE"), specializations(), admissions()]);
    return Object.fromEntries(eeVariants(programmes, specs, rounds));
  });
}
