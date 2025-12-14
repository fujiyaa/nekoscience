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

        unsafe { env::set_var("file_test", &file_path); }

        let fm = Arc::new(FileManager::new());

        let payload = json!({
            "key1": 42,
            "key2": "hello"
        });

        let insert_resp =
            insert_to_file(Path("file_test".to_string()), Json(payload), fm.clone()).await;

        let insert_current = insert_resp
            .current
            .get("current")
            .expect("insert response must contain 'current'")
            .as_object()
            .expect("'current' must be an object");

        assert!(insert_current.contains_key("key1"));
        assert!(insert_current.contains_key("key2"));

        let read_resp =
            read_file(Path("file_test".to_string()), fm.clone()).await;

        let read_current = read_resp
            .current
            .as_object()
            .expect("read response must be an object");

        assert_eq!(read_current.get("key1"), Some(&json!(42)));
        assert_eq!(read_current.get("key2"), Some(&json!("hello")));

        let remove_payload = json!({
            "key1": null
        });

        let remove_resp =
            remove_from_file(Path("file_test".to_string()), Json(remove_payload), fm.clone()).await;

        let remove_current = remove_resp
            .current
            .get("current")
            .expect("remove response must contain 'current'")
            .as_object()
            .expect("'current' must be an object");

        assert!(!remove_current.contains_key("key1"));
        assert!(remove_current.contains_key("key2"));
    }

    #[tokio::test]
    async fn test_invalid_payload() {
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("test_invalid.json");

        unsafe {
            env::set_var("file_test_invalid", &file_path);
        }

        let fm = Arc::new(FileManager::new());

        let payload = json!(["not", "an", "object"]);

        let insert_resp = insert_to_file(
            Path("file_test_invalid".to_string()),
            Json(payload.clone()),
            fm.clone(),
        )
        .await;

        let insert_err = insert_resp
            .current
            .get("error")
            .expect("insert must return error for invalid payload");

        assert_eq!(insert_err, "invalid payload");

        let remove_resp = remove_from_file(
            Path("file_test_invalid".to_string()),
            Json(payload),
            fm.clone(),
        )
        .await;

        let remove_err = remove_resp
            .current
            .get("error")
            .expect("remove must return error for invalid payload");

        assert_eq!(remove_err, "invalid payload");
    }
}
