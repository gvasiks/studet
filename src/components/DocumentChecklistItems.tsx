"use client";

import { useEffect, useState } from "react";

// Отметки «собрано» у чек-листа документов (шаг 3 плана для иностранцев).
// Единственная клиентская часть блока: список рисует сервер (ForeignDocuments),
// сюда приходят готовые подписи. Отметки хранятся в localStorage этой вкладки
// браузера: в них только ключи документов, никаких личных данных и
// экзаменов (правило о sessionStorage касается результатов экзаменов).

export type ChecklistGroup = {
  title: string;
  items: { id: string; label: string; condition: string | null; note: string | null }[];
};

export function DocumentChecklistItems({
  storageKey,
  groups,
  progressTemplate,
  notesLanguage,
}: {
  storageKey: string;
  groups: ChecklistGroup[];
  /** «{done} of {total} ready» */
  progressTemplate: string;
  /** Язык примечаний (язык источника) — для атрибута lang. */
  notesLanguage: string;
}) {
  const [checked, setChecked] = useState<string[]>([]);

  // Читаем после монтирования: на сервере localStorage нет, и первая
  // отрисовка должна совпасть с серверной (все пункты не отмечены).
  useEffect(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem(storageKey) ?? "[]");
      // eslint-disable-next-line react-hooks/set-state-in-effect -- одноразовое чтение сохранённых отметок
      if (Array.isArray(saved)) setChecked(saved.filter((value): value is string => typeof value === "string"));
    } catch {
      // повреждённая запись или запрет хранилища — просто без отметок
    }
  }, [storageKey]);

  function toggle(id: string) {
    const next = checked.includes(id) ? checked.filter((value) => value !== id) : [...checked, id];
    setChecked(next);
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(next));
    } catch {
      // хранилище недоступно — отметка живёт до перезагрузки
    }
  }

  const ids = groups.flatMap((group) => group.items.map((item) => item.id));
  const done = ids.filter((id) => checked.includes(id)).length;

  return (
    <>
      <p className="mt-3 text-sm font-medium text-zinc-700" aria-live="polite">
        {progressTemplate.replace("{done}", String(done)).replace("{total}", String(ids.length))}
      </p>
      {groups.map((group) => (
        <fieldset key={group.title} className="mt-4">
          <legend className="text-sm font-semibold text-zinc-900">{group.title}</legend>
          <ul className="mt-2 space-y-2">
            {group.items.map((item) => {
              const inputId = `${storageKey}:${item.id}`;
              return (
                <li key={item.id} className="flex gap-3">
                  <input
                    id={inputId}
                    type="checkbox"
                    checked={checked.includes(item.id)}
                    onChange={() => toggle(item.id)}
                    className="mt-0.5 h-5 w-5 shrink-0 accent-brand-dark"
                  />
                  <label htmlFor={inputId} className="text-sm text-zinc-800">
                    {item.label}
                    {item.condition && <span className="text-zinc-600"> — {item.condition}</span>}
                    {item.note && (
                      <span lang={notesLanguage} className="mt-0.5 block text-xs leading-relaxed text-zinc-600">
                        {item.note}
                      </span>
                    )}
                  </label>
                </li>
              );
            })}
          </ul>
        </fieldset>
      ))}
    </>
  );
}
