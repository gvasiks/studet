#!/usr/bin/env bash
# Обновить сайт на сервере: забрать свежий код, собрать, перезапустить.
# Запускать под root:   bash /srv/studypick/app/deploy/update.sh
#
# Сборка идёт в той же папке, из которой работает сайт: около минуты, пока
# она идёт, сайт может отвечать ошибками. Обновляйте, когда посетителей мало.
# Если сборка упала, служба не перезапускается: работает прежняя версия,
# но её файлы уже частично заменены — исправьте причину и запустите снова.
set -euo pipefail

# Всё тело — в функции: bash читает файл по мере выполнения, а `git pull`
# ниже может заменить этот самый файл. Функция прочитана целиком до запуска.
main() {

APP=/srv/studypick/app
ENV_FILE=/etc/studypick/env
NODE_BIN=/opt/node24/bin

if [ "$(id -u)" -ne 0 ]; then
  echo "Запустите под root: перезапуск службы требует прав администратора." >&2
  exit 1
fi

# Код забирает и собирает пользователь сайта, не root: в папке сайта не
# должно появляться файлов, которые служба потом не сможет прочитать.
runuser -u studypick -- bash -c "
  set -euo pipefail
  cd '$APP'
  export PATH='$NODE_BIN':\$PATH
  git pull --ff-only
  set -a; . '$ENV_FILE'; set +a
  # Адрес базы и ключ проверяются до сборки: с неверным адресом сборка
  # падает через несколько минут с малопонятным сообщением (так было при
  # первой выкладке 2026-10-09).
  case \"\${NEXT_PUBLIC_SUPABASE_URL:-}\" in
    https://*) ;;
    *) echo 'Остановлено: NEXT_PUBLIC_SUPABASE_URL в $ENV_FILE должен начинаться с https:// (без кавычек и пробелов).' >&2; exit 1 ;;
  esac
  if [ -z \"\${NEXT_PUBLIC_SUPABASE_ANON_KEY:-}\" ]; then
    echo 'Остановлено: в $ENV_FILE не задан NEXT_PUBLIC_SUPABASE_ANON_KEY.' >&2; exit 1
  fi
  npm ci
  npm run build
"

systemctl restart studypick

# Ждём, пока сайт начнёт отвечать, и говорим прямо, получилось или нет.
for attempt in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/lv || true)
  if [ "$code" = "200" ]; then
    echo "Готово: сайт отвечает (версия $(runuser -u studypick -- git -C "$APP" log -1 --format='%h %s'))."
    exit 0
  fi
  sleep 1
done

echo "Сайт не ответил за 30 секунд. Журнал: journalctl -u studypick -n 50 --no-pager" >&2
exit 1

}

main "$@"
