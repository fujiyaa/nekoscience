use std::{collections::HashMap, fs, path::PathBuf, sync::{Arc, Mutex}};
use serde_json::{Value, json};
use dotenv::from_path;
use std::env;

#[derive(Clone)]
pub struct FileManager {
    files: Arc<HashMap<String, PathBuf>>,
    locks: Arc<HashMap<String, Arc<Mutex<()>>>>,
}

impl FileManager {
    pub fn new() -> Self {
        let mut env_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        env_path.pop();
        env_path.push(".env");
        from_path(&env_path).ok();

        let mut map = HashMap::new();
        let mut locks = HashMap::new();

        let project_root = env_path.parent().unwrap();

        for (key, value) in env::vars() {
            if key.starts_with("file_") {
                let path = project_root.join(value); 

                map.insert(key.clone(), path);
                locks.insert(key, Arc::new(Mutex::new(())));
            }
        }

        Self {
            files: Arc::new(map),
            locks: Arc::new(locks),
        }
    }

    pub fn read(&self, id: &str) -> Value {
        let path = match self.files.get(id) {
            Some(p) => p,
            None => return json!({"error": "unknown_id"}),
        };

        let lock = self.locks.get(id).unwrap();
        let _guard = lock.lock().unwrap(); 

        if !path.exists() {
            fs::create_dir_all(path.parent().unwrap()).ok();
            fs::write(path, "{}").ok();
        }

        let content = fs::read_to_string(path).unwrap_or_else(|_| "{}".into());
        serde_json::from_str(&content).unwrap_or_else(|_| json!({}))
    }

    pub fn insert(&self, id: &str, key: &str, value: Value) -> Value {
        let path = match self.files.get(id) {
            Some(p) => p,
            None => return json!({"error": "unknown_id"}),
        };

        let lock = self.locks.get(id).unwrap();
        let _guard = lock.lock().unwrap();

        let mut content: serde_json::Map<String, Value> = match fs::read_to_string(path)
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
        {
            Some(Value::Object(map)) => map,
            _ => serde_json::Map::new(),
        };

        content.insert(key.to_string(), value);

        fs::create_dir_all(path.parent().unwrap()).ok();
        fs::write(path, serde_json::to_string_pretty(&Value::Object(content.clone())).unwrap())
            .expect("failed to write");

        json!({"status": "ok", "current": content})
    }

    pub fn remove(&self, id: &str, key: &str) -> Value {
        let path = match self.files.get(id) {
            Some(p) => p,
            None => return json!({"error": "unknown_id"}),
        };

        let lock = self.locks.get(id).unwrap();
        let _guard = lock.lock().unwrap();

        let mut content: serde_json::Map<String, Value> = match fs::read_to_string(path)
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
        {
            Some(Value::Object(map)) => map,
            _ => serde_json::Map::new(),
        };

        content.remove(key);

        fs::create_dir_all(path.parent().unwrap()).ok();
        fs::write(path, serde_json::to_string_pretty(&Value::Object(content.clone())).unwrap())
            .expect("failed to write");

        json!({"status": "ok", "current": content})
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use std::env;
    use std::sync::Arc;
    use std::thread;
    use tempfile::tempdir;
    use serde_json::json;

    #[test]
    fn test_file_manager_parallel_insert_remove() {
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("atomic.json");

        unsafe { env::set_var("FILE_ATOMIC", &file_path); }

        let manager = Arc::new(FileManager::new());

        let inserts = vec![
            ("apple", json!(1)),
            ("banana", json!(2)),
            ("cherry", json!(3)),
            ("banana2", json!(2)),
            ("cherry2", json!(3)),
            ("banana3", json!(2)),
            ("cherry3", json!(3)),
            ("banana4", json!(2)),
            ("cherry4", json!(3)),
            ("cherry5", json!(3)),
        ];

        let mut handles = vec![];
        for (key, value) in inserts {
            let mgr = Arc::clone(&manager);
            handles.push(thread::spawn(move || {
                mgr.insert("atomic", key, value);
            }));
        }

        for handle in handles {
            handle.join().unwrap();
        }

        let content = manager.read("atomic");
        let obj = content.as_object().unwrap();
        assert_eq!(obj.len(), 10);
        assert!(obj.contains_key("apple"));
        assert!(obj.contains_key("banana"));
        assert!(obj.contains_key("cherry"));

        let removes = vec!["banana", "banana2", "cherry", "cherry2", "cherry3"];

        let mut handles = vec![];
        for key in removes {
            let mgr = Arc::clone(&manager);
            let key = key.to_string();
            handles.push(thread::spawn(move || {
                mgr.remove("atomic", &key);
            }));
        }

        for handle in handles {
            handle.join().unwrap();
        }

        let final_content = manager.read("atomic");
        println!("{}", final_content);
        let final_obj = final_content.as_object().unwrap();
        assert_eq!(final_obj.len(), 5);
        assert!(final_obj.contains_key("apple"));
        assert!(!final_obj.contains_key("banana"));
        assert!(!final_obj.contains_key("cherry"));
    }
}
