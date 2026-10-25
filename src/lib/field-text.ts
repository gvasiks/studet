// Шрифт полей ввода на телефоне — не мельче 16px: Safari на iPhone при фокусе
// на поле с более мелким шрифтом сам увеличивает страницу, и её приходится
// уменьшать обратно (проверка 2026-10-25). С sm (640px) — обычный размер.
// Проверяет e2e/a11y.spec.ts («на телефоне без прокрутки вбок и поля от 16px»).
export const FIELD_TEXT = "text-base sm:text-sm";

// То же для полей HeroUI: размер текста у них задаётся в слоте input, и
// classNames перекрывает их собственный text-small.
export const HEROUI_FIELD_CLASSES = { input: "text-base sm:text-small" };
