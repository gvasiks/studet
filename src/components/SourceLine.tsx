import { InfoIcon } from "@/components/icons";

// Ссылка на норму под каждым фактом (правило 5 CLAUDE.md). Отдельный
// компонент, потому что повторяется на /rights, /glossary и /privacy, и
// выглядеть должен одинаково: это главный сигнал доверия на сайте, и он
// не должен читаться как обычный текст абзаца.
export function SourceLine({ label, value }: { label: string; value: string }) {
  return (
    <p className="mt-4 flex items-start gap-2 border-t border-zinc-100 pt-3 text-xs leading-relaxed text-zinc-600">
      <InfoIcon size={14} className="mt-px shrink-0 text-zinc-400" />
      <span>
        <span className="font-medium uppercase tracking-wide text-zinc-500">{label}</span>
        {": "}
        {value}
      </span>
    </p>
  );
}
