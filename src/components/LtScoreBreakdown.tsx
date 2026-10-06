import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import type { LtComponent, LtScoreItem } from "@/lib/lt-score";
import { interpolate } from "@/lib/outcomes";

// Разбор литовского балла по составляющим: что пошло в каждую, с каким
// весом и сколько дало. Один и тот же блок на странице расчёта по программе
// и в «куда я прохожу» — правило проекта: балл всегда показывается с
// разбором «из чего сложился».
export function LtScoreBreakdown({
  dict,
  language,
  components,
  items,
}: {
  dict: Dictionary;
  language: Language;
  components: readonly LtComponent[];
  items: LtScoreItem[];
}) {
  const text = dict.ltCalculator;
  const label = (subject: string) => text.subjects[subject as keyof typeof text.subjects] ?? subject;
  const number = (value: number) => value.toLocaleString(language, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <dl className="space-y-2 text-sm text-zinc-700">
      {items.map((item) => {
        const component = components.find((candidate) => candidate.position === item.position);
        const used = item.used.map(label).join(", ");
        return (
          <div key={item.position} className="flex flex-wrap justify-between gap-x-4">
            <dt>
              {interpolate(text.component, { n: String(item.position) })}
              {" · "}
              {interpolate(text.weight, { weight: item.weight.toLocaleString(language) })}
              <span className="block text-zinc-500">
                {item.value === null
                  ? text.notUsed
                  : `${used}${component?.mode === "average" ? ` (${text.average})` : ""} — ${number(item.value)}`}
              </span>
            </dt>
            <dd className="tabular-nums">{number(item.contribution)}</dd>
          </div>
        );
      })}
    </dl>
  );
}
