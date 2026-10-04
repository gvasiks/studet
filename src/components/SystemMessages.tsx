"use client";

import { createContext, useContext } from "react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";

// Тексты страниц «не найдено» и «ошибка».
//
// Next.js не передаёт этим страницам параметры маршрута, а error.tsx обязан
// быть клиентским компонентом — словарь (серверный) им недоступен. Поэтому
// раскладка сайта, которая язык знает, кладёт нужный кусок словаря в
// контекст, а not-found.tsx и error.tsx читают его отсюда. Так тексты
// остаются в словарях (правило 1 CLAUDE.md), и в браузер уходят только эти
// несколько строк, а не весь словарь.
type SystemMessages = { locale: Locale; messages: Dictionary["system"] };

const SystemMessagesContext = createContext<SystemMessages | null>(null);

export function SystemMessagesProvider({
  locale,
  messages,
  children,
}: SystemMessages & { children: React.ReactNode }) {
  return <SystemMessagesContext.Provider value={{ locale, messages }}>{children}</SystemMessagesContext.Provider>;
}

export function useSystemMessages(): SystemMessages {
  const value = useContext(SystemMessagesContext);
  if (!value) throw new Error("useSystemMessages: нет SystemMessagesProvider выше по дереву");
  return value;
}
