import type { Dictionary } from "@/i18n/dictionaries";

export function SiteFooter({ dict }: { dict: Dictionary }) {
  return (
    <footer className="mt-auto border-t border-zinc-200">
      <div className="page-container py-8">
        {/* zinc-600, не 500: на сером фоне страницы (zinc-100) 500 не дотягивает до 4.5:1 */}
        <p className="max-w-3xl text-xs leading-relaxed text-zinc-600">{dict.footer.disclaimer}</p>
      </div>
    </footer>
  );
}
