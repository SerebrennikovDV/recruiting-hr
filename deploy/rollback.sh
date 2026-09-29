#!/bin/bash
# Возврат рабочего стенда к предыдущей версии кода.
#
# Запуск на сервере:
#   bash /root/unithire/deploy/rollback.sh            на один коммит назад
#   bash /root/unithire/deploy/rollback.sh 1c5eff5    к указанному коммиту
#
# Откат меняет только код. Чтобы следующее обновление не вернуло
# ошибочную правку, её нужно отменить и в репозитории (git revert).
set -euo pipefail

main() {
    cd /root/unithire
    local target="${1:-HEAD~1}"

    echo "[1/4] Код версии $target"
    git reset --hard "$target"
    git log --oneline -1

    echo "[2/4] Сборка образа"
    docker compose build web

    echo "[3/4] Перезапуск"
    docker compose up -d
    docker compose exec -T web python manage.py collectstatic --noinput \
        > /dev/null

    echo "[4/4] Проверка"
    local code=""
    for _ in $(seq 1 30); do
        code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ \
               || true)
        if [ "$code" = "200" ]; then
            echo "Сайт отвечает: 200. Откат завершён."
            return 0
        fi
        sleep 2
    done
    echo "Сайт не отвечает (код $code). Логи: docker compose logs --tail 50 web"
    return 1
}

main "$@"
