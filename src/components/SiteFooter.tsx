import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { GraduationCapIcon, InfoIcon } from "@/components/icons";
import type { Tone } from "@/components/LocaleSwitcher";
import { SITE_NAME } from "@/lib/site";

export function SiteFooter({ dict, locale, tone }: { dict: Dictionary; locale: Locale; tone: Tone }) {
  if (tone === "light") {
    return (
      <footer className="mt-auto border-t border-zinc-200">
        <div className="page-container py-8">
          {/* zinc-600, не 500: на сером фоне страницы (zinc-100) 500 не дотягивает до 4.5:1 */}
          <p className="text-xs leading-relaxed text-zinc-600">{dict.footer.disclaimer}</p>
        </div>
      </footer>
    );
  }

  const links = [
    { href: `/${locale}/programmes`, label: dict.nav.catalog },
    { href: `/${locale}/survey`, label: dict.nav.survey },
    { href: `/${locale}/match`, label: dict.nav.match },
    { href: `/${locale}/favorites`, label: dict.favorites.navLink },
    { href: `/${locale}/glossary`, label: dict.nav.glossary },
    { href: `/${locale}/rights`, label: dict.nav.rights },
  ];

  return (
    <footer className="relative z-10 mt-auto border-t border-white/10 bg-black/20">
      <div className="page-container flex flex-col gap-6 py-8">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-brand text-white">
              <GraduationCapIcon size={15} />
            </span>
            <span className="text-sm font-bold text-white">{SITE_NAME}</span>
          </div>
          <nav aria-label={dict.nav.footer} className="mt-3">
            <ul className="flex flex-wrap gap-x-4 gap-y-2 text-xs">
              {links.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="text-slate-300 hover:text-white hover:underline">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
          <InfoIcon size={16} className="mt-0.5 shrink-0 text-sky-400" />
          <p className="text-xs leading-relaxed text-slate-400">{dict.footer.disclaimer}</p>
        </div>
      </div>
    </footer>
  );
}
