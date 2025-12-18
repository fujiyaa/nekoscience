use serde_json::{Value, json};
use sqlx::{SqlitePool, Row};
use std::sync::Arc;
use chrono::Utc;

#[derive(Clone)]
pub struct DbManager {
    pool: Arc<SqlitePool>,
}

impl DbManager {
    async fn exec(pool: &SqlitePool, sql: &str) -> anyhow::Result<()> {
    sqlx::query(sql).execute(pool).await?;
    Ok(())
    }

    pub async fn new(database_url: &str) -> anyhow::Result<Self> {
        let pool = SqlitePool::connect(database_url).await?;



        // users                    пользователи

        // threads                  треды и категория

        // posts                    посты и контент

        // thread_rating            рейтинг тредов

        // thread_aggregates        агр. кол-во постов и голосов

        // user_category_stats      агр. пользователей по категориям



        Self::exec(&pool, "PRAGMA foreign_keys = ON;").await?;

        Self::exec(&pool, r#"
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,                     -- автор (id)
                username TEXT NOT NULL,                     -- имя пользователя

                created_at INTEGER NOT NULL                 -- время добавления в базу
            );
        "#).await?;

        Self::exec(&pool, r#"
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY,                     -- id треда как на сайте                
                title TEXT NOT NULL,                        -- название треда
                author_id INTEGER NOT NULL,                 -- автор (id)

                state TEXT NOT NULL DEFAULT 'open',         -- open, locked, deleted
                is_archived INTEGER NOT NULL DEFAULT '0',   -- 0 или 1

                view_count_fallback INTEGER NOT NULL DEFAULT '0',    -- for future use TM
                post_count_fallback INTEGER NOT NULL DEFAULT '0',

                created_at INTEGER NOT NULL,                -- создан
                updated_at INTEGER NOT NULL DEFAULT '0',    -- последнее действие

                category TEXT NOT NULL DEFAULT 'all',       -- категория

                FOREIGN KEY(author_id) REFERENCES users(id)
            );
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_threads_created
            ON threads(created_at);
        "#).await?;

        Self::exec(&pool, r#"
            CREATE TABLE IF NOT EXISTS posts (                
                thread_id INTEGER NOT NULL,                 -- id треда как на сайте
                author_id INTEGER NOT NULL,                 -- автор (id)
                post_number INTEGER NOT NULL,               -- последовательность постов                

                state TEXT NOT NULL,                        -- ok, edited, deleted
                body_raw TEXT NOT NULL,                     -- html
                body_bbc TEXT NOT NULL,                     -- raw
            
                created_at INTEGER NOT NULL,                -- создан
                updated_at INTEGER NOT NULL DEFAULT '0',    -- последнее действие

                update_action TEXT NOT NULL DEFAULT '',     -- действие обновления                

                PRIMARY KEY(thread_id, post_number),
                FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE,
                FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE CASCADE
            );
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_posts_thread
            ON posts(thread_id);
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_posts_created
            ON posts(created_at);
        "#).await?;

        Self::exec(&pool, r#"
            CREATE TABLE IF NOT EXISTS thread_rating (
                thread_id INTEGER NOT NULL,
                user_id   INTEGER NOT NULL,
                value     INTEGER NOT NULL CHECK (value IN (-1, 1)),
                created_at INTEGER NOT NULL,

                PRIMARY KEY (thread_id, user_id),
                FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_votes_thread
            ON thread_rating(thread_id);
        "#).await?;
       
        Self::exec(&pool, r#"
        CREATE TABLE IF NOT EXISTS thread_aggregates (
            thread_id INTEGER NOT NULL,
            period_start INTEGER NOT NULL,              -- начало периода
            period_end INTEGER NOT NULL,                -- конец периода
            
            post_count INTEGER NOT NULL DEFAULT 0,
            score INTEGER NOT NULL DEFAULT 0,           -- сумма голосов (+1/-1)

            PRIMARY KEY(thread_id, period_start, period_end),
            FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
        );
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_thread_aggregates_thread_period
            ON thread_aggregates(thread_id, period_start, period_end);
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_thread_aggregates_period
            ON thread_aggregates(period_start, period_end);
        "#).await?;        

        Self::exec(&pool, r#"
        CREATE TABLE IF NOT EXISTS user_category_stats (
            user_id INTEGER NOT NULL,                   -- автор (id)
            category TEXT NOT NULL,                     -- категория треда
            period_start INTEGER NOT NULL,
            period_end INTEGER NOT NULL,

            post_count INTEGER NOT NULL DEFAULT 0,      -- количество постов в категории

            PRIMARY KEY(user_id, category, period_start, period_end),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_user_category_user_period
            ON user_category_stats(user_id, period_start, period_end);
        "#).await?;

        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_user_category_period
            ON user_category_stats(period_start, period_end);
        "#).await?;
        
        Self::exec(&pool, r#"
            CREATE INDEX IF NOT EXISTS idx_user_category_category_period
            ON user_category_stats(category, period_start, period_end);
        "#).await?;

        Ok(Self { pool: Arc::new(pool) })
    }


    pub async fn add_thread(&self, id: i64,  title: &str, author_id: &str) -> anyhow::Result<i64> {
        let created_at = Utc::now().timestamp();

        let row = sqlx::query(
            "INSERT INTO threads (id, title, author_id, created_at) VALUES (?, ?, ?, ?)"
        )
        .bind(id)
        .bind(title)
        .bind(author_id)
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

    pub async fn count_threads(&self) -> i64 {
        match sqlx::query("SELECT COUNT(*) as cnt FROM threads")
            .fetch_one(&*self.pool)
            .await
        {
            Ok(row) => row.get::<i64, _>("cnt"),
            Err(e) => {
                eprintln!("Failed to count threads: {}", e);
                0
            }
        }
    }

    // только для тестов
    #[allow(unused)]
    pub async fn close(&self) {
        self.pool.close().await;
    }
}



#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    async fn create_test_db() -> anyhow::Result<DbManager> {
        // в памяти SQLite
        let db = DbManager::new(":memory:").await?;
        
        // очищаем таблицы, если нужно
        sqlx::query("DELETE FROM posts").execute(&*db.pool).await?;
        sqlx::query("DELETE FROM threads").execute(&*db.pool).await?;
        sqlx::query("DELETE FROM thread_rating").execute(&*db.pool).await?;
        
        Ok(db)
    }

    #[tokio::test]
    async fn test_add_thread_and_check_exists() -> anyhow::Result<()> {
        let db = create_test_db().await?;

        let thread_id = 1;
        db.add_thread(thread_id, "Thread 1", "Alice").await?;

        println!("Thread count: {}", db.count_threads().await);

        assert!(db.thread_exists(thread_id).await);
        assert!(!db.thread_exists(thread_id + 1).await);

        Ok(())
    }


    #[tokio::test]
    async fn test_add_posts_and_count() -> anyhow::Result<()> {
        let db = create_test_db().await?;

        let thread_id = 1;
        db.add_thread(thread_id, "Thread 2", "Bob").await?;

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

        let thread_id = 2;
        db.add_thread(thread_id, "Thread 3", "Carol").await?;

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

        let thread_id = 3;
        db.add_thread(thread_id, "Thread 4", "Dave").await?;

        let res = db.add_posts(thread_id, &[]).await;
        assert_eq!(res.get("inserted").unwrap().as_i64().unwrap(), 0);

        let count = db.count_posts(thread_id).await;
        assert_eq!(count, 0);

        Ok(())
    }

}
