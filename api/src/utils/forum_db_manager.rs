use serde_json::{Value, json};
use sqlx::{SqlitePool, Row};
use std::sync::Arc;
use chrono::Utc;

#[derive(Clone)]
pub struct DbManager {
    pool: Arc<SqlitePool>,
}

impl DbManager {
    pub async fn new(database_url: &str) -> anyhow::Result<Self> {
        let pool = SqlitePool::connect(database_url).await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            "#
        ).execute(&pool).await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
            )
            "#
        ).execute(&pool).await?;

        Ok(Self { pool: Arc::new(pool) })
    }

    pub async fn add_thread(&self, title: &str, author: &str) -> anyhow::Result<i64> {
        let created_at = Utc::now().timestamp();
        let row = sqlx::query(
            "INSERT INTO threads (title, author, created_at) VALUES (?, ?, ?)"
        )
        .bind(title)
        .bind(author)
        .bind(created_at)
        .execute(&*self.pool)
        .await?;

        Ok(row.last_insert_rowid())
    }

    pub async fn add_posts(&self, thread_id: i64, posts: &[Value]) -> Value {
        let mut tx = match self.pool.begin().await {
            Ok(t) => t,
            Err(e) => return json!({"error": e.to_string()}),
        };

        let mut inserted = 0;

        for post in posts {
            let author = post.get("author").and_then(|v| v.as_str()).unwrap_or("");
            let body = post.get("body").and_then(|v| v.as_str()).unwrap_or("");
            let created_at = Utc::now().timestamp();

            if let Err(e) = sqlx::query(
                "INSERT INTO posts (thread_id, author, body, created_at) VALUES (?, ?, ?, ?)"
            )
            .bind(thread_id)
            .bind(author)
            .bind(body)
            .bind(created_at)
            .execute(&mut *tx)
            .await
            {
                eprintln!("Failed to insert post: {}", e);
                continue;
            }

            inserted += 1;
        }

        if let Err(e) = tx.commit().await {
            return json!({"error": e.to_string()});
        }

        json!({"inserted": inserted})
    }

    pub async fn get_posts(&self, thread_id: i64, limit: i64, offset: i64) -> Vec<Value> {
        let rows = match sqlx::query(
            "SELECT id, author, body, created_at FROM posts WHERE thread_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?"
        )
        .bind(thread_id)
        .bind(limit)
        .bind(offset)
        .fetch_all(&*self.pool)
        .await
        {
            Ok(r) => r,
            Err(e) => {
                eprintln!("Failed to fetch posts: {}", e);
                return vec![];
            }
        };

        rows.into_iter()
            .map(|row| {
                json!({
                    "id": row.get::<i64, _>("id"),
                    "author": row.get::<String, _>("author"),
                    "body": row.get::<String, _>("body"),
                    "created_at": row.get::<i64, _>("created_at"),
                })
            })
            .collect()
    }

    pub async fn count_posts(&self, thread_id: i64) -> i64 {
        match sqlx::query("SELECT COUNT(*) as cnt FROM posts WHERE thread_id = ?")
            .bind(thread_id)
            .fetch_one(&*self.pool)
            .await
        {
            Ok(row) => row.get::<i64, _>("cnt"),
            Err(_) => 0,
        }
    }

    pub async fn thread_exists(&self, thread_id: i64) -> bool {
        match sqlx::query("SELECT 1 FROM threads WHERE id = ?")
            .bind(thread_id)
            .fetch_optional(&*self.pool)
            .await
        {
            Ok(Some(_)) => true,
            _ => false,
        }
    }
}



#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    const USE_FILE_DB: bool = true; // true - в файл

    async fn create_test_db() -> anyhow::Result<DbManager> {
        let database_url = if USE_FILE_DB {
            use std::fs;
            use std::path::PathBuf;

            // потом поменять на env
            let mut path = PathBuf::from("E:\\fa\\nekoscience\\storage\\tests");
            fs::create_dir_all(&path)?; 

            path.push("test_in_forum_db_manager.db");

            if !path.exists() {
                fs::File::create(&path)?;
            }

            path.to_str().unwrap().to_string()
        } else {
            ":memory:".to_string()
        };

        let db = DbManager::new(&database_url).await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            "#
        )
        .execute(&*db.pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(thread_id) REFERENCES threads(id)
            )
            "#
        )
        .execute(&*db.pool)
        .await?;

        sqlx::query("DELETE FROM posts").execute(&*db.pool).await?;
        sqlx::query("DELETE FROM threads").execute(&*db.pool).await?;

        Ok(db)
    }


    #[tokio::test]
    async fn test_add_thread_and_check_exists() -> anyhow::Result<()> {
        let db = create_test_db().await?;

        let thread_id = db.add_thread("Thread 1", "Alice").await?;
        assert!(thread_id > 0);

        assert!(db.thread_exists(thread_id).await);
        assert!(!db.thread_exists(thread_id + 1).await);

        Ok(())
    }

    #[tokio::test]
    async fn test_add_posts_and_count() -> anyhow::Result<()> {
        let db = create_test_db().await?;

        let thread_id = db.add_thread("Thread 2", "Bob").await?;

        let posts = vec![
            json!({"author": "Alice", "body": "Hello"}),
            json!({"author": "Bob", "body": "World"}),
        ];

        let res = db.add_posts(thread_id, &posts).await;
        assert_eq!(res.get("inserted").unwrap().as_i64().unwrap(), 2);

        let count = db.count_posts(thread_id).await;
        assert_eq!(count, 2);

        Ok(())
    }

    #[tokio::test]
    async fn test_get_posts_batch() -> anyhow::Result<()> {
        let db = create_test_db().await?;

        let thread_id = db.add_thread("Thread 3", "Carol").await?;

        let posts = (1..=5)
            .map(|i| json!({"author": format!("User{}", i), "body": format!("Post {}", i)}))
            .collect::<Vec<_>>();

        db.add_posts(thread_id, &posts).await;

        let batch1 = db.get_posts(thread_id, 3, 0).await;
        assert_eq!(batch1.len(), 3);
        assert_eq!(batch1[0]["author"], "User1");
        assert_eq!(batch1[2]["author"], "User3");

        let batch2 = db.get_posts(thread_id, 3, 3).await;
        assert_eq!(batch2.len(), 2);
        assert_eq!(batch2[0]["author"], "User4");
        assert_eq!(batch2[1]["author"], "User5");

        Ok(())
    }

    #[tokio::test]
    async fn test_add_posts_empty_array() -> anyhow::Result<()> {
        let db = create_test_db().await?;

        let thread_id = db.add_thread("Thread 4", "Dave").await?;
        let res = db.add_posts(thread_id, &[]).await;

        assert_eq!(res.get("inserted").unwrap().as_i64().unwrap(), 0);

        let count = db.count_posts(thread_id).await;
        assert_eq!(count, 0);

        Ok(())
    }
}
