"use client";

// Стирает введённые экзамены из вкладки (exam-session.ts) — в «Kur var
// iestāties» и в калькуляторе. Обычная кнопка, без HeroUI: действие одно.
export function ClearExamsButton({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <button
      type="button"
      onClick={onClear}
      className="inline-flex h-8 shrink-0 items-center rounded-full border border-zinc-200 bg-white px-3 text-[13px] font-medium text-zinc-700 shadow-control transition-colors hover:border-zinc-300 hover:text-zinc-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
    >
      {label}
    </button>
  );
}
