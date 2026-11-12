// Arteliq desktop shell: window + tray + service lifecycle only. All logic and the whole UI live in Arteliq
// (the dashboard served by `arteliq web`); the Python backend ships as a PyInstaller sidecar next to the app.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::{AppHandle, Manager, RunEvent, WebviewWindow, WindowEvent};

const DEFAULT_PORT: u16 = 8765;
const READY_TIMEOUT: Duration = Duration::from_secs(60);

#[derive(Default)]
struct Service {
    /// The sidecar this app started. Never set for a dashboard we merely attached to.
    child: Mutex<Option<Child>>,
    url: Mutex<Option<String>>,
}

fn log(msg: &str) {
    eprintln!("[arteliq-desktop] {msg}");
}

/// GET /api/ready on 127.0.0.1:port; true when an Arteliq dashboard answers 200.
fn ready(port: u16) -> bool {
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let Ok(mut s) = TcpStream::connect_timeout(&addr, Duration::from_secs(1)) else { return false };
    let _ = s.set_read_timeout(Some(Duration::from_secs(2)));
    let req = format!("GET /api/ready HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n\r\n");
    if s.write_all(req.as_bytes()).is_err() {
        return false;
    }
    let mut buf = Vec::new();
    let _ = s.read_to_end(&mut buf);
    buf.starts_with(b"HTTP/1.0 200") || buf.starts_with(b"HTTP/1.1 200")
}

fn configured_port() -> u16 {
    std::env::var("ARTEL_PORT").ok().and_then(|v| v.trim().parse().ok()).unwrap_or(DEFAULT_PORT)
}

fn free_port() -> std::io::Result<u16> {
    Ok(TcpListener::bind("127.0.0.1:0")?.local_addr()?.port())
}

fn sidecar_path(app: &AppHandle) -> Result<PathBuf, String> {
    let name = if cfg!(windows) { "arteliq.exe" } else { "arteliq" };
    let mut candidates = Vec::new();
    if let Ok(p) = std::env::var("ARTELIQ_SIDECAR") {
        candidates.push(PathBuf::from(p));
    }
    if let Ok(dir) = app.path().resource_dir() {
        candidates.push(dir.join("sidecar").join(name));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            candidates.push(dir.join("sidecar").join(name));
        }
    }
    candidates.iter().find(|p| p.is_file()).cloned().ok_or_else(|| format!("не найден файл службы Arteliq ({name})"))
}

/// Start `arteliq web --port N` (it never opens a browser) and wait for /api/ready. Returns the dashboard URL.
fn start_sidecar(app: &AppHandle) -> Result<String, String> {
    let svc = app.state::<Service>();
    let exe = sidecar_path(app)?;
    let port = free_port().map_err(|e| e.to_string())?;
    let mut cmd = Command::new(&exe);
    cmd.args(["web", "--port", &port.to_string()]).stdin(Stdio::null()).stdout(Stdio::null());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
    }
    let mut child = cmd.spawn().map_err(|e| format!("не удалось запустить службу: {e}"))?;
    let started = Instant::now();
    while !ready(port) {
        if let Ok(Some(status)) = child.try_wait() {
            return Err(format!("служба завершилась при запуске ({status})"));
        }
        if started.elapsed() > READY_TIMEOUT {
            let _ = child.kill();
            return Err("служба не ответила за 60 секунд".into());
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    *svc.child.lock().unwrap() = Some(child);
    let url = format!("http://127.0.0.1:{port}/");
    log(&format!("sidecar ready on {url}"));
    Ok(url)
}

/// Attach to a dashboard already running on the configured port, else start our own sidecar.
fn connect(app: &AppHandle) -> Result<String, String> {
    let port = configured_port();
    if ready(port) {
        let url = format!("http://127.0.0.1:{port}/");
        log(&format!("attached to {url}"));
        return Ok(url);
    }
    start_sidecar(app)
}

/// Stop the sidecar we started (SIGINT first so the dashboard shuts its kernel down cleanly). No-op when attached.
fn stop_sidecar(app: &AppHandle) {
    let svc = app.state::<Service>();
    let Some(mut child) = svc.child.lock().unwrap().take() else { return };
    #[cfg(unix)]
    {
        let _ = Command::new("kill").args(["-INT", &child.id().to_string()]).status();
        let t = Instant::now();
        while t.elapsed() < Duration::from_secs(5) {
            if matches!(child.try_wait(), Ok(Some(_))) {
                return;
            }
            std::thread::sleep(Duration::from_millis(100));
        }
    }
    let _ = child.kill();
    let _ = child.wait();
}

fn show_message(win: &WebviewWindow, text: &str) {
    let js = format!("document.getElementById('m')&&(document.getElementById('m').textContent={:?})", text);
    let _ = win.eval(&js);
}

fn open_dashboard(app: &AppHandle) {
    log("starting");
    let Some(win) = app.get_webview_window("main") else {
        log("main window is missing");
        return;
    };
    match connect(app) {
        Ok(url) => {
            *app.state::<Service>().url.lock().unwrap() = Some(url.clone());
            if let Ok(u) = url.parse() {
                let _ = win.navigate(u);
            }
        }
        Err(e) => {
            log(&e);
            show_message(&win, &format!("Не удалось запустить Arteliq: {e}"));
        }
    }
}

fn focus(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| focus(app)))
        .manage(Service::default())
        .setup(|app| {
            let open = MenuItem::with_id(app, "open", "Открыть Arteliq", true, None::<&str>)?;
            let toggle = MenuItem::with_id(app, "toggle", "Остановить службу", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Выход", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&open, &toggle, &quit])?;
            let toggle_item = toggle.clone();
            let mut tray = TrayIconBuilder::new().menu(&menu).tooltip("Arteliq");
            if let Some(icon) = app.default_window_icon() {
                tray = tray.icon(icon.clone());
            }
            tray.on_menu_event(move |app, event| match event.id().as_ref() {
                "open" => focus(app),
                "quit" => {
                    stop_sidecar(app);
                    app.exit(0);
                }
                "toggle" => {
                    let app = app.clone();
                    let item = toggle_item.clone();
                    std::thread::spawn(move || {
                        let running = app.state::<Service>().url.lock().unwrap().is_some();
                        if running {
                            stop_sidecar(&app);
                            *app.state::<Service>().url.lock().unwrap() = None;
                            let _ = item.set_text("Запустить службу");
                            if let Some(w) = app.get_webview_window("main") {
                                if let Ok(u) = "tauri://localhost/index.html".parse() {
                                    let _ = w.navigate(u);
                                }
                                std::thread::sleep(Duration::from_millis(500));
                                show_message(&w, "Служба остановлена. Трей → «Запустить службу».");
                            }
                        } else {
                            let _ = item.set_text("Остановить службу");
                            open_dashboard(&app);
                        }
                    });
                }
                _ => {}
            })
            .on_tray_icon_event(|tray, event| {
                if let tauri::tray::TrayIconEvent::DoubleClick { .. } = event {
                    focus(tray.app_handle());
                }
            })
            .build(app)?;
            let handle = app.handle().clone();
            std::thread::spawn(move || open_dashboard(&handle));
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close(); // closing hides to the tray; «Выход» is the only way out
                let _ = window.hide();
            }
        })
        .build(tauri::generate_context!())
        .expect("failed to build the Arteliq desktop shell");
    app.run(|app, event| {
        if let RunEvent::Exit = event {
            stop_sidecar(app);
        }
    });
}
