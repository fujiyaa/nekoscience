use axum::{Router, routing::get};
use std::{collections::HashMap, net::SocketAddr, sync::Arc};
use dotenv::dotenv;
use std::env;

mod api_keys; 
mod pp_calc;
mod mods_parser;

use api_keys::{AppState, check_api_key_with_state, handler};
use pp_calc::calculate_pp_handler;


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

    // строим роутер и добавляем middleware
    let app = Router::new()
        .route("/", get(handler))
        .route("/pp", axum::routing::post(calculate_pp_handler))  // <- новый маршрут
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
