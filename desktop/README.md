# Arteliq Desktop

Настоящее приложение для компьютера: своё окно, значок в панели задач/Dock, иконка в трее, установщик.
Оболочка (Tauri v2, Rust) — только окно, трей и жизненный цикл службы. Вся логика и весь интерфейс остаются в
Arteliq: окно показывает ту же панель, что отдаёт `arteliq web`. Бэкенд едет внутри приложения как sidecar
(PyInstaller, onedir, точка входа `artel.cli:main`).

## Как это работает

1. При запуске оболочка проверяет `GET /api/ready` на `127.0.0.1:$ARTEL_PORT` (по умолчанию 8765). Если панель уже
   отвечает — подключается к ней (и при выходе её не трогает).
2. Иначе выбирает свободный порт, запускает sidecar `arteliq web --port N` (браузер `web` никогда не открывает),
   ждёт `/api/ready` и открывает окно на этом адресе.
3. Второй запуск приложения выводит на передний план уже открытое окно.
4. Трей: «Открыть Arteliq», «Остановить службу» / «Запустить службу», «Выход». Закрытие окна прячет его в трей.
   «Выход» останавливает только тот sidecar, который запустило приложение.

## Сборка локально

Нужны: Python 3.10+, Node 20+, Rust (stable) и системные библиотеки Tauri
(Linux: `libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev patchelf libxdo-dev libssl-dev`).

```
pip install -e . pyinstaller
python desktop/sidecar/build.py          # -> desktop/sidecar/dist/arteliq/
cd desktop && npm install
npx tauri build --bundles appimage,deb   # Windows: nsis, macOS: dmg
```

Для запуска без установки: `ARTELIQ_SIDECAR=/путь/к/arteliq npx tauri dev`.
Иконки: `pip install cairosvg pillow && python desktop/scripts/make_icons.py` (из `docs/brand/arteliq-mark.svg`;
сгенерированные файлы лежат в `desktop/src-tauri/icons/` и закоммичены).

CI: `.github/workflows/desktop.yml` на пуши в `feat/native-desktop` и `release/v*` собирает sidecar и пакеты для
трёх ОС и кладёт их в артефакты запуска. На Linux дополнительно запускает собранный бинарник под xvfb на 20 секунд и
проверяет, что sidecar ответил на `/api/ready`. GitHub Releases пока не создаются.

## Что не подписано и какие предупреждения увидите

Все сборки неподписанные.

- **Windows (NSIS .exe):** SmartScreen — «Windows защитил ваш компьютер» → «Подробнее» → «Выполнить в любом случае».
  Установка в профиль пользователя, права администратора не нужны.
- **macOS (.dmg):** Gatekeeper — «приложение повреждено / не удаётся проверить разработчика». Перетащите Arteliq в
  «Программы», затем: ПКМ → «Открыть», либо `xattr -dr com.apple.quarantine /Applications/Arteliq.app`.
- **Linux (AppImage / deb):** предупреждений нет. AppImage: `chmod +x` и запуск (нужен FUSE 2, иначе
  `--appimage-extract-and-run`). deb: `sudo apt install ./Arteliq_*.deb`.

## Известные ограничения

- Системные уведомления идут через Web Notification API внутри webview, моста нет. Windows (WebView2): работает.
  macOS (WKWebView): API недоступен, уведомлений не будет. Linux (WebKitGTK): как правило недоступен. Нативный
  мост — отдельный шаг.
- На Linux значок в трее требует среды с поддержкой AppIndicator (в GNOME нужно расширение); без него остаётся
  окно, а «закрыть в трей» прячет окно без способа вернуть его, кроме повторного запуска приложения.
- Sidecar не умеет запускать «самого себя» как `python -m ...` (замороженный интерпретатор): функции, которые
  порождают `sys.executable -m artel`, в приложении не проверялись.
- Автообновления нет: приложение обновляется вместе с Arteliq (новой сборкой).
- Подписание (Windows/macOS) и нотаризация не настроены.
- `Cargo.lock` и `package-lock.json` не закоммичены (в контейнере разработки нет Rust/npm-реестра): CI берёт
  последние версии зависимостей v2.
