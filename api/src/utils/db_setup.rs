// src/utils/db_setup.rs
use crate::utils::forum_db_manager::DbManager;
use std::sync::Arc;
use std::path::{Path, PathBuf};
use std::fs;
use dotenv::from_path;

pub async fn init_forum_db<P: AsRef<Path>>(relative_path: P) -> anyhow::Result<(Arc<DbManager>, PathBuf)> {
    let mut env_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    env_path.pop(); 
    env_path.push(".env");
    from_path(&env_path).ok();
   
    let mut db_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    db_path.pop();
    db_path.push(relative_path);

    if let Some(parent) = db_path.parent() {
        fs::create_dir_all(parent).unwrap();
    }
    if !db_path.exists() {
        fs::File::create(&db_path).unwrap();
    }

    let db = DbManager::new(db_path.to_str().unwrap())
        .await
        .expect("Failed to connect DB");

    Ok((Arc::new(db), db_path.canonicalize()?))
}



#[cfg(test)]
mod tests {
    use super::*;
    use tokio;

    #[tokio::test]
    async fn test_init_forum_db_creates_file() {
        let test_db_path = "storage/tests/testing_only_do_not_edit.db";

        let (db, abs_path) = init_forum_db(test_db_path).await.unwrap();

        assert!(std::path::Path::new(&abs_path).exists());

        let thread_id = db.add_thread("Test Thread", "Fujiya").await.unwrap();
        assert!(thread_id > 0);

        let count = db.count_posts(thread_id).await;
        assert_eq!(count, 0);
        
        db.close().await;
        drop(db);
        let _ = std::fs::remove_file(&abs_path);
    }
}
