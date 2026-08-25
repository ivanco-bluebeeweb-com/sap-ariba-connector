# SAP Ariba Connector — идеальный первый запуск

Источник: `ONBOARDING_FIRST_LAUNCH_STANDARD.md`. Целевой пользователь: процурмент-
офицер, AP-аналитик или category manager, впервые открывающий приложение.

## 1. Credential type
OAuth2 Client Credentials, realm-scoped: realm/site id (Ariba tenant identifier) +
OAuth app key/secret + сгенерированный API key (SAP API Business Hub apikey header),
полученные через SAP Ariba Developer Portal (developer.ariba.com) для конкретного realm.

## 2. Идеальный флоу (без ограничений SDK)
1. **Первое открытие** — простыми словами объяснить, что такое "realm": "ID вашего
   Ariba-сайта, например AN01000000042-T — найдите его в Ariba admin под System
   Realm Information".
2. **Форма подключения** — realm id + OAuth application key/secret + API key,
   без прыжков между экранами.
3. **После успеха** — сразу пробный вызов к каждому лицензированному API-пакету
   (Requisitions/POs/Suppliers/Sourcing/Contracts) и явная карта "что включено для
   этого realm", а не предположение, что всё доступно — SAP Ariba лицензирует
   модули отдельно per customer contract.
4. **Живая сводка** — открытые requisitions, ожидающие approval POs, активные
   sourcing события — сразу actionable, не пустой экран.
5. **Ошибка "package not licensed"** — отдельное явное сообщение с указанием,
   какой именно API-пакет недоступен для этого realm и что нужно уточнить у
   SAP Ariba account team, а не общий 403.
6. **Multi-realm** — если у консультанта несколько realm'ов клиентов (production +
   test realm — Ariba всегда даёт пару), явный переключатель между сохранёнными
   подключениями с пометкой "Test" / "Production".
7. **cXML предупреждение** — явно объяснить в help-диалоге, что punchout/order/
   invoice через cXML не входит в это приложение (см. `CONNECTOR_DISCOVERY.md` §3),
   чтобы пользователь не ждал функциональности, которой здесь не будет.

## 3. Разница с реализацией сейчас
См. `UI_COMPONENT_PLAN.md` §0 — реализация ограничена тем, что фактически
возвращает realm через `audit_ariba_access` (используется общий SDK `DataTable`
вместо специализированной "лицензионной карты"), и multi-realm переключатель
использует обычный список подключений вместо визуального Test/Production badge.
