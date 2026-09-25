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
  // Миграция 20260924180000: verification_queue (анонимно читаемое view)
  // больше не отдаёт текст причины — он мог содержать сам неподтверждённый
  // факт (например, коэффициенты формулы), см. комментарий в миграции.
  // Поле оставлено в типе ради формы API, но через этот путь всегда null;
  // настоящая причина — в исходной таблице, смотреть в Studio.
  disputedReason: string | null;
};

// Приоритет по спросу — прямое указание ревью 2026-09, пункт 03: РТУ
// и ЛУ сопоставимы по числу заявок, но покрытие формул сейчас сильно
// перекошено в пользу ЛУ (было собрано в первую очередь, потому что
// удобнее, не потому что нужнее). Запасной порядок для вузов, для
// которых пока нет известного срока подачи (см. ниже) — всё остальное
// идёт следом по алфавиту slug.
const UNIVERSITY_PRIORITY: Record<string, number> = { rtu: 0, lu: 1 };

function priority(universitySlug: string): number {
  return UNIVERSITY_PRIORITY[universitySlug] ?? 2;
}

export const getVerificationQueue = cache(async (): Promise<VerificationQueueItem[]> => {
  const [{ data, error }, earliestOpensBySlug] = await Promise.all([
    supabase
      .from("verification_queue")
      .select(
        "fact_id, fact_type, programme_id, programme_name, university_slug, university_name, collected_at, source_url, item_count, protocol_complete, protocol_missing, source_doc_date, disputed_at, disputed_reason",
      ),
    getEarliestOpensBySlug(),
  ]);

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
    // План 2026-09-21, разбор бизнес-процессов, предложение №3: у вуза с
    // известной (подтверждённой — см. getEarliestOpensBySlug) датой
    // открытия регистрации факты подтверждаются раньше, чем у вуза, чей
    // срок ещё дальше или вовсе неизвестен — иначе в декабре, когда в
    // очереди разом копится порция 2 требований и обновлённые формулы,
    // часы владельца идут по порядку добавления записи, а не по тому,
    // где дедлайн ближе.
    const opensA = earliestOpensBySlug.get(a.universitySlug);
    const opensB = earliestOpensBySlug.get(b.universitySlug);
    if (opensA && opensB && opensA !== opensB) return opensA < opensB ? -1 : 1;
    if (opensA && !opensB) return -1;
    if (!opensA && opensB) return 1;

    const priorityDiff = priority(a.universitySlug) - priority(b.universitySlug);
    if (priorityDiff !== 0) return priorityDiff;
    // Старые несобранные записи — вперёд, чтобы ничего не забывалось.
    return new Date(a.collectedAt).getTime() - new Date(b.collectedAt).getTime();
  });
});

// Самая ранняя известная дата открытия регистрации на вуз. Только
// ПОДТВЕРЖДЁННЫЕ строки — этот запрос идёт через анонимный ключ (тот же
// клиент, что у публичных страниц), а RLS application_round
// (application_round_public_read, verified_at is not null) неподтверждённые
// черновые даты и не отдаст. Сигнал уже полезен и в таком урезанном виде:
// как только срок вуза подтверждён, его оставшиеся факты в очереди
// подтверждения поднимаются наверх сами, без ручной перестановки.
async function getEarliestOpensBySlug(): Promise<Map<string, string>> {
  const { data, error } = await supabase
    .from("application_round")
    .select("opens_on, university:university_id(slug)")
    .not("opens_on", "is", null);

  if (error) throw error;

  const earliest = new Map<string, string>();
  for (const row of data ?? []) {
    const slug = (row.university as unknown as { slug: string } | null)?.slug;
    if (!slug || !row.opens_on) continue;
    const current = earliest.get(slug);
    if (!current || row.opens_on < current) earliest.set(slug, row.opens_on);
  }
  return earliest;
}

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
