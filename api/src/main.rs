use axum::{Router, routing::get};
use std::{collections::HashMap, net::SocketAddr, sync::Arc};
use dotenv::dotenv;
use std::env;

mod api_keys; 
mod models;
mod handlers;
mod utils;

use api_keys::{AppState, check_api_key_with_state, handler};
use handlers::score_pp::calculate_score_pp;
use handlers::pp_parts::calculate_pp_parts;

#[tokio::main]
async fn main() {
    dotenv().ok();
    // создаём "базу" ключей. Можно потом загружать из конфига или БД.
    let mut keys_map = HashMap::new();
    
    let password = env::var("LOCAL_API_KEY").expect("LOCAL_API_KEY not set");
    let host = env::var("NEKO_HOST").unwrap_or("localhost".to_string());

    keys_map.insert(password, host);

    let state = AppState {
        keys: Arc::new(keys_map),
        log_path: "access.log".to_string(),
    };

    let app = Router::new()
        .route("/", get(handler))
        .route("/score-pp", axum::routing::post(calculate_score_pp))
        .route("/pp-parts", axum::routing::post(calculate_pp_parts))  
        .layer(axum::middleware::from_fn_with_state(
            state.clone(),
            check_api_key_with_state,
        ));   

    let addr = SocketAddr::from(([127, 0, 0, 1], 5727));
    println!("Listening on http://{}", addr);

    // запуск сервера
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
