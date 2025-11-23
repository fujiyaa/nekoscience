use axum::{Router, routing::get};
use std::{collections::HashMap, net::SocketAddr, sync::Arc};
use dotenv::dotenv;
use std::env;

mod api_keys; 
mod models;
mod calculators;
mod utils;
mod systems;

use api_keys::{AppState, check_api_key_with_state, handler};
use calculators::score_pp::calculate_score_pp;
use calculators::pp_parts::calculate_pp_parts;
use calculators::map_stats::calculate_map_stats;
use utils::file_manager::FileManager;

use crate::systems::file_endpoints::read_file;
use crate::systems::file_endpoints::insert_to_file;
use crate::systems::file_endpoints::remove_from_file;
use axum::routing::{post};

#[tokio::main]
async fn main() {
    dotenv().ok();
    let mut keys_map = HashMap::new();
    
    let password = env::var("LOCAL_API_KEY").expect("LOCAL_API_KEY not set");
    let host = env::var("NEKO_HOST").unwrap_or("localhost".to_string());

    keys_map.insert(password, host);

    let fm = Arc::new(FileManager::new());

    let state = AppState {
        keys: Arc::new(keys_map),
        log_path: "access.log".to_string(),
    };

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


        .layer(axum::middleware::from_fn_with_state(
            state.clone(),
            check_api_key_with_state,
        ));   

    let addr = SocketAddr::from(([127, 0, 0, 1], 5727));
    println!("Listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
