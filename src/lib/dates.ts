// Дата для показа на сайте — одно место на все страницы.
//
// Английский по умолчанию в браузерах и в Node — американский: «10/6/2026»,
// и латвийский, литовский или эстонский читатель понимает это как 10 июня,
// а не 6 октября. Поэтому у английского дата пишется с названием месяца
// («6 Oct 2026»): её не спутать ни при каком привычном порядке. У остальных
// языков — их обычная запись цифрами («6.10.2026.»).
//
// Сокращения месяцев — свои, а не из браузера: часть дат показывают
// клиентские компоненты (калькулятор, список сохранённых), и если браузер
// сократит сентябрь иначе, чем сервер («Sep» и «Sept»), React сообщит о
// несовпадении разметки.
//
// timeZone — для моментов времени, у которых важен день в конкретной стране
// (конец подачи в Эстонии — по таллинскому времени); без него — часовой пояс
// сервера, как было.
const ENGLISH_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatDate(value: string | Date, language: string, timeZone?: string): string {
  const date = typeof value === "string" ? new Date(value) : value;
  if (language === "en") {
    const parts = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "numeric", year: "numeric", timeZone }).formatToParts(date);
    const part = (type: string) => Number(parts.find((item) => item.type === type)?.value);
    return `${part("day")} ${ENGLISH_MONTHS[part("month") - 1]} ${part("year")}`;
  }
  return date.toLocaleDateString(language, { timeZone });
}
