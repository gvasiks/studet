import { supabase } from "@/lib/supabase";
import { listProgrammes } from "@/lib/catalog";
import { remember } from "@/lib/server-memo";
import { admissionYear, eeVariants, tallinnYear, type EeAdmissionYear, type EeVariant } from "@/lib/ee-variants";

// Подписи версий одного учебного плана у эстонских программ (ee-variants.ts):
// id программы -> чем она отличается от двойника. Только у программ с
// двойником — около 160 строк. Из памяти сервера на пять минут, как
// остальные данные каталога (server-memo.ts). Объект общий для всех
// запросов — только читать.

// PostgREST отдаёт не больше тысячи строк за запрос.
const PAGE_ROWS = 1000;

type FieldRow = { programme_id: string; specialization: string | null; portal_created_at?: string | null };

// Специализация и дата записи на портале — из ee_programme_field. 42703 —
// колонки ещё нет (миграции 20261123130000 / 20261127120000 не применены):
// тогда читаем без неё, и подписи по ней не появляются.
async function fieldRows(): Promise<FieldRow[]> {
  for (const columns of ["programme_id, specialization, portal_created_at", "programme_id, specialization"]) {
    const rows: FieldRow[] = [];
    let missingColumn = false;
    for (let from = 0; ; from += PAGE_ROWS) {
      const { data, error } = await supabase
        .from("ee_programme_field")
        .select(columns)
        .order("programme_id")
        .range(from, from + PAGE_ROWS - 1);
      if (error?.code === "42703") {
        missingColumn = true;
        break;
      }
      if (error) throw error;
      rows.push(...(data as unknown as FieldRow[]));
      if (data.length < PAGE_ROWS) break;
    }
    if (!missingColumn) return rows;
  }
  return [];
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
    const [programmes, fields, rounds] = await Promise.all([listProgrammes("EE"), fieldRows(), admissions()]);
    const specs = new Map<string, string>();
    const portalYears = new Map<string, number>();
    for (const row of fields) {
      if (row.specialization) specs.set(row.programme_id, row.specialization);
      if (row.portal_created_at) portalYears.set(row.programme_id, tallinnYear(row.portal_created_at));
    }
    return Object.fromEntries(eeVariants(programmes, specs, rounds, portalYears));
  });
}
