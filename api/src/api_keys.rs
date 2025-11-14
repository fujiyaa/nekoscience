use axum::{
    extract::State,
    http::{Request, StatusCode},
    middleware::Next,
    response::Response,
    Json,
};
use chrono::Local;
use serde::Serialize;
use std::{collections::HashMap, sync::Arc};
use tokio::fs::OpenOptions;
use tokio::io::AsyncWriteExt;
use serde_json::json;

// Состояние приложения
#[derive(Clone)]
pub struct AppState {
    pub keys: Arc<HashMap<String, String>>,
    pub log_path: String,
}

// Пример handler
#[derive(Serialize)]
pub struct MyResponse {
    message: String,
    value: i32,
    flag: bool,
}

pub async fn handler() -> Json<MyResponse> {
    Json(MyResponse {
        message: "Секретный контент".to_string(),
        value: 42,
        flag: true,
    })
}

// Middleware для проверки ключа и логирования
pub async fn check_api_key_with_state(
    State(state): State<AppState>,
    req: Request<axum::body::Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    let key_opt = req
        .headers()
        .get("X-API-Key")
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_owned());

    let method = req.method().to_string();
    let path = req.uri().path().to_string();

    let ts = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

    if let Some(key) = key_opt {
        if let Some(username) = state.keys.get(&key) {
            let log_json = json!({
                "user": username,
                "key": key,
                "method": method,
                "path": path
            });
            let log_line = format!("{ts} {}\n", log_json.to_string());
            let _ = append_log(&state.log_path, log_line.clone()).await;
            println!("{}", log_line.trim_end());
            return Ok(next.run(req).await);
        } else {
            let log_json = json!({
                "user": "UNKNOWN_KEY",
                "key": key,
                "method": method,
                "path": path
            });
            let log_line = format!("{ts} {}\n", log_json.to_string());
            let _ = append_log(&state.log_path, log_line.clone()).await;
            eprintln!("{}", log_line.trim_end());
            return Err(StatusCode::UNAUTHORIZED);
        }
    } else {
        let log_json = json!({
            "user": "NO_KEY",
            "key": null,
            "method": method,
            "path": path
        });
        let log_line = format!("{ts} {}\n", log_json.to_string());
        let _ = append_log(&state.log_path, log_line.clone()).await;
        eprintln!("{}", log_line.trim_end());
        return Err(StatusCode::UNAUTHORIZED);
    }
}

// Функция для записи лога в файл
async fn append_log(path: &str, line: String) -> Result<(), std::io::Error> {
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .await?;
    file.write_all(line.as_bytes()).await?;
    Ok(())
}
