import { cache } from "react";
import { supabase } from "@/lib/supabase";

export type VerificationQueueItem = {
  factId: string;
  factType: "formula" | "application_round" | "admission_type" | "programme_field" | "programme_requirement";
  programmeId: string | null;
  programmeName: string | null;
  universitySlug: string;
  universityName: string;
  collectedAt: string;
  sourceUrl: string | null;
  // Для programme_field одна строка на вуз — сколько программ ждут проверки;
  // для остальных типов всегда 1.
  itemCount: number;
  // Только для формул (иначе null): полон ли протокол источника — номер и
  // дата документа, копия в репозитории — и чего не хватает. Дата — версия
  // документа (у документа с поправками дата последней). Пока протокол
  // неполон, база не даст поставить verified_at.
  protocolComplete: boolean | null;
  protocolMissing: string | null;
  sourceDocDate: string | null;
  // План 2026-09-21, пункт 03: третье состояние факта — уже разобрана
  // человеком или осторожной автоматикой, подтвердить нельзя, потому что
  // сам документ неоднозначен (не путать с protocolMissing — там
  // неполный протокол источника, здесь источник полон, но не однозначен).
  // Не альтернатива verified_at — запись остаётся неподтверждённой.
  disputedAt: string | null;
  disputedReason: string | null;
};

// Приоритет по спросу — прямое указание ревью 2026-09, пункт 03: РТУ
// и ЛУ сопоставимы по числу заявок, но покрытие формул сейчас сильно
// перекошено в пользу ЛУ (было собрано в первую очередь, потому что
// удобнее, не потому что нужнее). Всё, чего нет в списке, идёт следом
// по алфавиту slug.
const UNIVERSITY_PRIORITY: Record<string, number> = { rtu: 0, lu: 1 };

function priority(universitySlug: string): number {
  return UNIVERSITY_PRIORITY[universitySlug] ?? 2;
}

export const getVerificationQueue = cache(async (): Promise<VerificationQueueItem[]> => {
  const { data, error } = await supabase
    .from("verification_queue")
    .select(
      "fact_id, fact_type, programme_id, programme_name, university_slug, university_name, collected_at, source_url, item_count, protocol_complete, protocol_missing, source_doc_date, disputed_at, disputed_reason",
    );

  if (error) throw error;

  const items: VerificationQueueItem[] = (data ?? []).map((row) => ({
    factId: row.fact_id,
    factType: row.fact_type,
    programmeId: row.programme_id,
    programmeName: row.programme_name,
    universitySlug: row.university_slug,
    universityName: row.university_name,
    collectedAt: row.collected_at,
    sourceUrl: row.source_url,
    itemCount: row.item_count,
    protocolComplete: row.protocol_complete,
    protocolMissing: row.protocol_missing,
    sourceDocDate: row.source_doc_date,
    disputedAt: row.disputed_at,
    disputedReason: row.disputed_reason,
  }));

  return items.sort((a, b) => {
    const priorityDiff = priority(a.universitySlug) - priority(b.universitySlug);
    if (priorityDiff !== 0) return priorityDiff;
    // Старые несобранные записи — вперёд, чтобы ничего не забывалось.
    return new Date(a.collectedAt).getTime() - new Date(b.collectedAt).getTime();
  });
});

export type VerificationHealth = {
  verifiedFormulas: number;
  totalFormulas: number;
};

// "Доля критичных полей, проверенных..." (ревью, пункт 03) — здесь
// сужено до формул: это единственный из критичных фактов (правило 6),
// у которого сегодня вообще есть неподтверждённые строки в БД
// (application_round/admission_type только что заведены и пока почти
// пустые). Окно "за последние 90 дней" из ревью пока не считаем
// отдельно — подтверждённых записей ещё 0, отслеживать свежесть
// подтверждения не с чем; вернуться к этому, когда появится история.
export const getVerificationHealth = cache(async (): Promise<VerificationHealth> => {
  const [{ count: verifiedFormulas, error: formulaError }, queue] = await Promise.all([
    supabase.from("formula").select("id", { count: "exact", head: true }),
    getVerificationQueue(),
  ]);

  if (formulaError) throw formulaError;

  const unverifiedFormulas = queue.filter((item) => item.factType === "formula").length;

  return {
    verifiedFormulas: verifiedFormulas ?? 0,
    totalFormulas: (verifiedFormulas ?? 0) + unverifiedFormulas,
  };
});
