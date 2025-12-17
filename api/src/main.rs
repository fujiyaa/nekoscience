use axum::{Router, routing::{get, post}};
use std::{collections::HashMap, net::SocketAddr, sync::Arc};
use dotenv::dotenv;
use std::env;

mod api_keys; 
mod models;
mod calculators;
mod utils;
mod systems;
mod external;

use api_keys::{AppState, check_api_key_with_state, handler};
use calculators::score_pp::calculate_score_pp;
use calculators::pp_parts::calculate_pp_parts;
use calculators::map_stats::calculate_map_stats;
use utils::file_manager::FileManager;
use utils::db_setup::init_forum_db;
use utils::osu_api_setup::init_osu_api;

use crate::systems::file_endpoints::read_file;
use crate::systems::file_endpoints::insert_to_file;
use crate::systems::file_endpoints::remove_from_file;

use crate::systems::forum_db_endpoints::add_thread;
use crate::systems::forum_db_endpoints::add_posts_batch;
use crate::systems::forum_db_endpoints::read_posts_batch;
use crate::systems::forum_db_endpoints::thread_exists;
use crate::systems::forum_db_endpoints::thread_stats;
use crate::systems::forum_db_endpoints::thread_count;



#[tokio::main]
async fn main() {
    dotenv().ok();
    let mut keys_map = HashMap::new();
    
    let password = env::var("LOCAL_API_KEY").expect("LOCAL_API_KEY not set");
    let host = env::var("NEKO_HOST").unwrap_or("localhost".to_string());

    keys_map.insert(password, host);

    let fm = Arc::new(FileManager::new());
    
    let forum_db = env::var("FORUM_DB").expect("FORUM_DB not set");
    let (db, _abs_path) = init_forum_db(&forum_db).await.unwrap();

    let api = init_osu_api().await.unwrap();

    let state = AppState {
        keys: Arc::new(keys_map),
        log_path: "access.log".to_string(), 
    };

    let forum_routes = Router::new()
    .route("/thread", post({
        let db = db.clone();
        let api = api.clone();
        move |path| add_thread(path, db.clone(), api.clone())
    }))
    .route("/thread/{id}/exists", get({
        let db = db.clone();
        move |path| thread_exists(path, db.clone())
    }))
    .route("/thread/{id}/posts/add", get({
        let db = db.clone();
        move |path, payload| add_posts_batch(path, payload, db.clone())
    }))
    .route("/thread/{id}/posts/read", post({
        let db = db.clone();
        move |path, payload| read_posts_batch(path, payload, db.clone())
    }))
    .route("/thread/{id}/stats", get({
        let db = db.clone();
        move |path| thread_stats(path, db.clone())
    }))
    .route("/thread/count/threads/{dummy}", get({
        let db = db.clone();
        move |path| thread_count(path, db.clone())
    }));

    let app = Router::new()
        .route("/", get(handler))
        .route("/score-pp", post(calculate_score_pp))
        .route("/pp-parts", post(calculate_pp_parts))
        .route("/map-stats", post(calculate_map_stats))
        .route("/file/{id}", get({
            let fm = fm.clone();
            move |path| read_file(path, fm.clone())
        }))
        .route("/file/{id}/insert", post({
            let fm = fm.clone();
            move |path, payload| insert_to_file(path, payload, fm.clone())
        }))
        .route("/file/{id}/remove", post({
            let fm = fm.clone();
            move |path, payload| remove_from_file(path, payload, fm.clone())
        }))

        .nest("/forum", forum_routes)

        .with_state(db.clone())

        .layer(axum::middleware::from_fn_with_state(
            state.clone(),
            check_api_key_with_state,
        ));   

    let addr = SocketAddr::from(([127, 0, 0, 1], 5727));
    println!("Listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
