use axum::Json;
use serde_json::json;
use std::collections::HashMap;

use crate::models::{ScoreInput, to_score, GameMode, Skills};
use rosu_pp::Beatmap;

#[derive(serde::Deserialize)]
pub struct SkillsRequest {
    pub mode: String, // "Osu", "Taiko", "Catch", "Mania"
    pub scores: Vec<ScoreInput>,
}

pub async fn calculate_pp_parts(
    Json(payload): Json<SkillsRequest>
) -> Json<serde_json::Value> {

    // 1️⃣ Определяем игровой режим
    let mode = match GameMode::from_str(&payload.mode) {
        Some(m) => m,
        None => return Json(json!({"error": "Invalid mode"})),
    };

    // 2️⃣ Загружаем карты из кэша
    let mut maps: HashMap<u32, Beatmap> = HashMap::new();
    for score in &payload.scores {
        let path = format!(r"E:\fa\nekoscience\bot\src\cache\beatmaps\{}.osu", score.map_id);
        if let Ok(map) = Beatmap::from_path(&path) {
            maps.insert(score.map_id, map);
        } else {
            eprintln!("Failed to load map: {}", path);
        }
    }

    // 3️⃣ Преобразуем ScoreInput в Score
    let scores: Vec<_> = payload.scores.iter().map(to_score).collect();

    // 4️⃣ Вычисляем навыки
    let skills = Skills::calculate(mode, &scores, maps);

    // 5️⃣ Формируем JSON для ответа
    let result = match skills {
        Skills::Osu { acc, aim, speed, acc_total, aim_total, speed_total } => json!({
            "acc": acc,
            "aim": aim,
            "speed": speed,
            "acc_total": acc_total,
            "aim_total": aim_total,
            "speed_total": speed_total,
        }),
        Skills::Taiko { acc, strain } => json!({ "acc": acc, "strain": strain }),
        Skills::Catch { acc, movement } => json!({ "acc": acc, "movement": movement }),
        Skills::Mania { acc, strain } => json!({ "acc": acc, "strain": strain }),
    };

    Json(result)
}
