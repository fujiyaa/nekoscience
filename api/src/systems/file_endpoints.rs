use axum::{extract::Path, Json};
use serde::Serialize;
use serde_json::{Value, json};
use std::sync::Arc;
use crate::utils::file_manager::FileManager;

#[derive(Serialize)]
pub struct PpResponse {
    pub status: String,
    pub current: Value,
}

pub async fn read_file(path: Path<String>, fm: Arc<FileManager>) -> Json<PpResponse> {
    let id = path.0;
    let content = fm.read(&id);

    // не нужна ошибка потому файлы создаются из ограниченного списка

    Json(PpResponse {
        status: "ok".to_string(),
        current: content,
    })
}

pub async fn insert_to_file(path: Path<String>, Json(payload): Json<Value>, fm: Arc<FileManager>) -> Json<PpResponse> {
    let id = path.0;
    let mut last_result = Value::Null;

    if let Some(obj) = payload.as_object() {
        for (k, v) in obj {
            last_result = fm.insert(&id, k, v.clone());
        }
    } else {
        last_result = json!({"error": "invalid payload"});
    }

    Json(PpResponse {
        status: "ok".to_string(),
        current: last_result,
    })
}

pub async fn remove_from_file(
    path: Path<String>,
    Json(payload): Json<Value>,
    fm: Arc<FileManager>,
) -> Json<PpResponse> {
    let id = path.0;
    let mut last_result = Value::Null;

    if let Some(obj) = payload.as_object() {
        for (k, _) in obj {
            last_result = fm.remove(&id, k);
        }
    } else {
        last_result = json!({"error": "invalid payload"});
    }

    Json(PpResponse {
        status: "ok".to_string(),
        current: last_result,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use serde_json::json;
    use std::sync::Arc;
    use std::env;
    use axum::extract::Path;
    use axum::Json;

    #[tokio::test]
    async fn test_insert_read_remove() {
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("test.json");

        unsafe { env::set_var("FILE_TEST", &file_path); }

        let fm = Arc::new(FileManager::new());

        let payload = json!({"key1": 42, "key2": "hello"});
        let insert_resp = insert_to_file(Path("test".to_string()), Json(payload), fm.clone()).await;
        let current = insert_resp.current.as_object().unwrap();
        assert!(current.contains_key("key1"));
        assert!(current.contains_key("key2"));

        let read_resp = read_file(Path("test".to_string()), fm.clone()).await;
        let current = read_resp.current.as_object().unwrap();
        assert_eq!(current.get("key1").unwrap(), &json!(42));
        assert_eq!(current.get("key2").unwrap(), &json!("hello"));

        let remove_payload = json!({"key1": null});
        let remove_resp = remove_from_file(Path("test".to_string()), Json(remove_payload), fm.clone()).await;
        let current = remove_resp.current.as_object().unwrap();
        assert!(!current.contains_key("key1"));
        assert!(current.contains_key("key2"));
    }

    #[tokio::test]
    async fn test_invalid_payload() {
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("test_invalid.json");
        unsafe { env::set_var("FILE_TEST_INVALID", &file_path); }

        let fm = Arc::new(FileManager::new());

        let payload = json!(["not", "an", "object"]);
        let insert_resp = insert_to_file(Path("test_invalid".to_string()), Json(payload.clone()), fm.clone()).await;
        assert!(insert_resp.current.get("error").is_some());

        let remove_resp = remove_from_file(Path("test_invalid".to_string()), Json(payload.clone()), fm.clone()).await;
        assert!(remove_resp.current.get("error").is_some());
    }
}
