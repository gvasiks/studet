import type { Dictionary } from "@/i18n/dictionaries";

export function SiteFooter({ dict }: { dict: Dictionary }) {
  return (
    <footer className="border-t border-zinc-200 px-6 py-8">
      <p className="mx-auto max-w-3xl text-xs leading-relaxed text-zinc-500">
        {dict.footer.disclaimer}
      </p>
    </footer>
  );
}
