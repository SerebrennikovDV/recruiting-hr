"""
Корневая схема маршрутов проекта.

Подключает панель администратора Django и маршруты основного приложения core,
а в режиме отладки — раздачу загруженных пользователями медиафайлов (резюме).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Заголовки панели администратора (выводятся в шапке Django admin).
admin.site.site_header = "UnitHire — панель администратора"
admin.site.site_title = "UnitHire admin"
admin.site.index_title = "Управление рекрутинговой ИС ООО «ЮНИТКОД»"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]

# В режиме разработки Django сам отдаёт медиафайлы; в продакшене это делает
# хостинг/диск. Статику в продакшене отдаёт WhiteNoise.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
