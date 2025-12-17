use axum::{extract::Path, Json};
use serde::Serialize;
use serde_json::{Value, json};
use std::sync::Arc;
use crate::utils::forum_db_manager::DbManager;
use crate::external::osu_forum_api::OsuApi;

#[derive(Debug, Serialize)]
pub struct PpResponse {
    pub status: String,
    pub current: Value,
}

// pub async fn add_thread(
//     Json(payload): Json<Value>,
//     db: Arc<DbManager>,
// ) -> Json<PpResponse> {
//     let mut result = Value::Null;

//     if let (Some(id),Some(title), Some(author)) = (
//         payload.get("id").and_then(|v| v.as_i64()),
//         payload.get("title").and_then(|v| v.as_str()),
//         payload.get("author").and_then(|v| v.as_str())
//     ) {
//         match db.add_thread(id, title, author).await {
//             Ok(thread_id) => result = json!({ "thread_id": thread_id }),
//             Err(e) => result = json!({ "error": e.to_string() }),
//         }
//     } else {
//         result = json!({ "error": "invalid payload" });
//     }

//     Json(PpResponse {
//         status: "ok".to_string(),
//         current: result,
//     })
// }

pub async fn add_thread(
    Json(payload): Json<Value>,
    db: Arc<DbManager>,
    osu_api: Arc<OsuApi>,
) -> Json<PpResponse> {
    let mut result = Value::Null;

    let id = payload.get("id").and_then(|v| v.as_i64());
    let title;
    let author;

    if let Some(id) = id {
        match osu_api.get_topic(id as u64, None, Some(1), None, None, None).await {
            Ok(Some(topic_resp)) => {
                title = topic_resp.topic.title.clone();
                author = topic_resp.topic.user_id.to_string();
            }
            Ok(None) => {
                result = json!({ "error": "forum is private or restricted" });
                return Json(PpResponse {
                    status: "ok".to_string(),
                    current: result,
                });
            }
            Err(e) => {
                result = json!({ "error": format!("failed to fetch topic: {:?}", e) });
                return Json(PpResponse {
                    status: "ok".to_string(),
                    current: result,
                });
            }
        }

        match db.add_thread(id, &title, &author).await {
            Ok(thread_id) => result = json!({ "thread_id": thread_id }),
            Err(e) => result = json!({ "error": e.to_string() }),
        }
    } else {
        result = json!({ "error": "invalid payload: missing id" });
    }

    Json(PpResponse {
        status: "ok".to_string(),
        current: result,
    })
}


pub async fn thread_exists(
    path: Path<i64>,
    db: Arc<DbManager>,
) -> Json<PpResponse> {
    let thread_id = path.0;
    let exists = db.thread_exists(thread_id).await;

    Json(PpResponse {
        status: "ok".to_string(),
        current: json!({ "exists": exists }),
    })
}

pub async fn add_posts_batch(
    path: Path<i64>,              // thread_id
    Json(payload): Json<Value>,
    db: Arc<DbManager>,
) -> Json<PpResponse> {
    let thread_id = path.0;
    let mut last_result = Value::Null;

    if let Some(posts) = payload.get("posts").and_then(|v| v.as_array()) {
        last_result = db.add_posts(thread_id, posts).await;
    } else {
        last_result = json!({"error": "invalid payload"});
    }

    Json(PpResponse {
        status: "ok".to_string(),
        current: last_result,
    })
}

pub async fn read_posts_batch(
    path: Path<i64>,
    Json(payload): Json<Value>,
    db: Arc<DbManager>,
) -> Json<PpResponse> {
    let thread_id = path.0;

    let limit = payload.get("limit").and_then(|v| v.as_u64()).unwrap_or(50);
    let offset = payload.get("offset").and_then(|v| v.as_u64()).unwrap_or(0);

    let posts = db.get_posts(thread_id, limit as i64, offset as i64).await;

    Json(PpResponse {
        status: "ok".to_string(),
        current: json!({ "posts": posts }),
    })
}

pub async fn thread_stats(
    path: Path<i64>,
    db: Arc<DbManager>,
) -> Json<PpResponse> {
    let thread_id = path.0;

    let count = db.count_posts(thread_id).await;

    Json(PpResponse {
        status: "ok".to_string(),
        current: json!({ "post_count": count }),
    })
}

pub async fn thread_count(
    Path(_dummy): Path<String>,
    db: Arc<DbManager>,
) -> Json<PpResponse> {
    let count = db.count_threads().await;

    Json(PpResponse {
        status: "ok".to_string(),
        current: json!({ "thread_count": count }),
    })
}

// Вообще надо такто убрать методы по db. и оставить только API (срочно)
#[cfg(test)]
mod api_tests {
    use super::*;
    use crate::utils::forum_db_manager::DbManager;
    use axum::extract::Path;
    use axum::Json;
    use serde_json::json;
    use std::sync::Arc;
    use crate::utils::osu_api_setup::init_osu_api;
 
    async fn setup_db() -> Arc<DbManager> {
        const USE_FILE_DB: bool = false; // false для :memory:

        let database_url = if USE_FILE_DB {

            // потом поменять на env
            let mut path = std::path::PathBuf::from("E:\\fa\\nekoscience\\storage\\tests");
            std::fs::create_dir_all(&path).unwrap();

            path.push("test_in_forum_db_endpoints.db");

            if !path.exists() {
                std::fs::File::create(&path).unwrap();
            }

            path.to_str().unwrap().to_string()
        } else {
            ":memory:".to_string()
        };

        Arc::new(DbManager::new(&database_url).await.unwrap())
}

    fn clone_path(p: &Path<i64>) -> Path<i64> {
        Path(p.0)
    }

#[tokio::test]
async fn test_add_thread_and_exists() {
    let db = setup_db().await;

    let api: Arc<OsuApi> = init_osu_api().await.expect("Failed to init OsuApi");

    let topic_id = 2162723;

    let payload = json!({
        "id": topic_id,
        "title": "Test Thread",
        "author": "Alice"
    });

    let resp = add_thread(Json(payload), db.clone(), Arc::clone(&api)).await;
    println!("Response: {:?}", resp);

    let thread_id = resp
        .current
        .get("thread_id")
        .expect("No thread_id in response")
        .as_i64()
        .expect("thread_id is not i64");

    let exists_resp = thread_exists(Path(thread_id), db.clone()).await;
    assert!(
        exists_resp.current.get("exists").unwrap().as_bool().unwrap(),
        "Thread should exist"
    );
}



    #[tokio::test]
    async fn test_add_posts_batch_and_stats() {
        let db = setup_db().await;
        
        let real_id = 1;
        let thread_id = db.add_thread(real_id, "Batch Test", "Bob").await.unwrap();
        let path = Path(thread_id);

        let payload = json!({
            "posts": [
                {"author": "Alice", "body": "Hello"},
                {"author": "Bob", "body": "World"}
            ]
        });

        let resp = add_posts_batch(clone_path(&path), Json(payload), db.clone()).await;
        assert_eq!(resp.current.get("inserted").unwrap().as_i64().unwrap(), 2);

        let stats = thread_stats(clone_path(&path), db.clone()).await;
        assert_eq!(stats.current.get("post_count").unwrap().as_i64().unwrap(), 2);
    }

    #[tokio::test]
    async fn test_read_posts_batch_with_limit_offset() {
        let db = setup_db().await;

        let real_id = 2;
        let thread_id = db.add_thread(real_id, "Read Test", "Carol").await.unwrap();
        let path = Path(thread_id);

        let posts = vec![
            json!({"author": "Alice", "body": "Post1"}),
            json!({"author": "Bob", "body": "Post2"}),
            json!({"author": "Carol", "body": "Post3"}),
        ];
        db.add_posts(thread_id, &posts).await;

        let payload = json!({"limit": 2, "offset": 1});
        let resp = read_posts_batch(clone_path(&path), Json(payload), db.clone()).await;
        let fetched = resp.current.get("posts").unwrap().as_array().unwrap();

        assert_eq!(fetched.len(), 2);
        assert_eq!(fetched[0]["author"], "Bob");
        assert_eq!(fetched[1]["author"], "Carol");
    }

    #[tokio::test]
    async fn test_invalid_payload_add_posts() {
        let db = setup_db().await;

        let real_id = 3;
        let thread_id = db.add_thread(real_id, "Invalid Test", "Dave").await.unwrap();
        let path = Path(thread_id);

        let payload = json!({"invalid": []});
        let resp = add_posts_batch(path, Json(payload), db.clone()).await;

        assert!(resp.current.get("error").is_some());
    }

    #[tokio::test]
    async fn test_add_get_posts_large_batch() {
        let db = setup_db().await;

        let real_id = 2;
        let thread_id = db.add_thread(real_id, "Large Batch", "Eve").await.unwrap();
        let path = Path(thread_id);

        let posts: Vec<_> = (1..=105)
            .map(|i| json!({"author": format!("Author{}", i), "body": format!("Post body {}", i)}))
            .collect();

        let payload = json!({"posts": posts});
        let resp = add_posts_batch(clone_path(&path), Json(payload), db.clone()).await;
        assert_eq!(resp.current.get("inserted").unwrap().as_i64().unwrap(), 105);

        let stats = thread_stats(clone_path(&path), db.clone()).await;
        assert_eq!(stats.current.get("post_count").unwrap().as_i64().unwrap(), 105);

        let mut all_fetched = Vec::new();
        let mut offset = 0;
        let batch_size = 50;

        loop {
            let payload = json!({ "limit": batch_size, "offset": offset });
            let resp = read_posts_batch(clone_path(&path), Json(payload), db.clone()).await;
            let batch = resp.current.get("posts").unwrap().as_array().unwrap();

            if batch.is_empty() {
                break;
            }

            all_fetched.extend_from_slice(batch);
            offset += batch.len();
        }

        assert_eq!(all_fetched.len(), 105);

        for (i, post) in all_fetched.iter().enumerate() {
            assert_eq!(post["author"], format!("Author{}", i + 1));
            assert_eq!(post["body"], format!("Post body {}", i + 1));
        }
    }

    // #[tokio::test]
    // async fn test_add_posts_to_existing_thread_via_api() -> anyhow::Result<()> {
    //     let db = setup_db().await;

    //     let thread_payload = json!({
    //         "id": 5,
    //         "title": "Custom Title",
    //         "author": "Fujiya"
    //     });
    //     let thread_resp = add_thread(Json(thread_payload), db.clone()).await;
    //     let thread_id = thread_resp.current.get("thread_id").unwrap().as_i64().unwrap();
    //     let path = Path(thread_id);

    //     let new_posts_payload = json!({
    //         "posts": [
    //             { "author": "Fujiya1", "body": "Text post 1" },
    //             { "author": "Fujiya2", "body": "Text post 2" }
    //         ]
    //     });
    //     let add_resp = add_posts_batch(clone_path(&path), Json(new_posts_payload), db.clone()).await;
    //     assert_eq!(add_resp.current.get("inserted").unwrap().as_i64().unwrap(), 2);

    //     let stats = thread_stats(clone_path(&path), db.clone()).await;
    //     let post_count = stats.current.get("post_count").unwrap().as_i64().unwrap();
    //     assert_eq!(post_count, 2);

    //     let read_payload = json!({ "limit": 10, "offset": 0 });
    //     let fetched_resp = read_posts_batch(clone_path(&path), Json(read_payload), db.clone()).await;
    //     let fetched_posts = fetched_resp.current.get("posts").unwrap().as_array().unwrap();

    //     assert_eq!(fetched_posts.len(), 2);
    //     assert_eq!(fetched_posts[0]["author"], "Fujiya1");
    //     assert_eq!(fetched_posts[0]["body"], "Text post 1");
    //     assert_eq!(fetched_posts[1]["author"], "Fujiya2");
    //     assert_eq!(fetched_posts[1]["body"], "Text post 2");

    //     Ok(())
    // }
}

