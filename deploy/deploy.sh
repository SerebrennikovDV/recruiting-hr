#!/bin/bash
# Обновление рабочего стенда из репозитория GitHub.
#
# Запуск на сервере:  bash /root/unithire/deploy/deploy.sh
#
# Порядок: резервная копия базы, свежий код, сборка образа, перезапуск,
# миграции, статика, проверка ответа сайта. Если сайт после обновления
# не ответил, вернуть прежнюю версию: bash deploy/rollback.sh
#
# Тело обёрнуто в функцию: git обновляет и этот файл, а bash читает
# функцию целиком до запуска, поэтому обновление не ломает выполнение.
set -euo pipefail

main() {
    cd /root/unithire

    echo "[1/7] Резервная копия базы"
    /usr/local/bin/unithire-backup.sh
    tail -n 1 /root/backups/backup.log

    echo "[2/7] Код из GitHub"
    git fetch --quiet origin main
    git merge --ff-only origin/main
    git log --oneline -1

    echo "[3/7] Сборка образа"
    docker compose build web

    echo "[4/7] Перезапуск"
    docker compose up -d

    echo "[5/7] Миграции базы"
    docker compose exec -T web python manage.py migrate --noinput

    echo "[6/7] Статика"
    docker compose exec -T web python manage.py collectstatic --noinput \
        > /dev/null

    echo "[7/7] Проверка"
    check_site
}

check_site() {
    local code=""
    for _ in $(seq 1 30); do
        code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ \
               || true)
        if [ "$code" = "200" ]; then
            echo "Сайт отвечает: 200. Обновление завершено."
            return 0
        fi
        sleep 2
    done
    echo "Сайт не отвечает (код $code). Откат: bash deploy/rollback.sh"
    return 1
}

main "$@"
