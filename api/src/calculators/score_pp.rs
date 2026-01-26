use axum::{Json, extract::Json as AxumJson};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use crate::utils::mods_parser;

#[derive(Deserialize)]
pub struct PpRequest {
    pub map_path: String, 

    pub n300: Option<u32>, 
    pub n100: Option<u32>,
    pub n50: Option<u32>,
    pub misses: Option<u32>,

    pub mods: Option<String>, 
    pub combo: Option<u32>,
    pub accuracy: Option<f64>,

    pub lazer: Option<bool>,
    pub clock_rate: Option<f64>, 

    pub custom_ar: Option<f32>,
    pub custom_cs: Option<f32>,
    pub custom_hp: Option<f32>,
    pub custom_od: Option<f32>,
}

#[derive(Serialize, Default)]
pub struct PpResponse {
    pub pp: f64,
    pub no_choke_pp: f64,
    pub perfect_pp: f64,

    pub star_rating: f64,
    pub perfect_combo: u32,
    pub expected_bpm: f64,
}

pub async fn calculate_score_pp(
    AxumJson(payload): AxumJson<PpRequest>
) -> Json<PpResponse> {
    // let base_folder = std::env::var("BEATMAP_CACHE_PATH")
    // .expect("BEATMAP_CACHE_PATH is not set");

    let base_folder = r"E:\fa\nekoscience\bot\src\cache\beatmaps";

    let mut map_path = PathBuf::from(base_folder);
    map_path.push(format!("{}.osu", payload.map_path));

    let map = match rosu_pp::Beatmap::from_path(&map_path) {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Failed to load beatmap from {}: {:?}", map_path.display(), e);
            return Json(PpResponse::default());
        }
    };

    if let Err(e) = map.check_suspicion() {
        eprintln!("Beatmap suspicion check failed for {}: {:?}", map_path.display(), e);
        return Json(PpResponse::default());
    }


    let mods_str = payload.mods.unwrap_or("NM".to_string());
    let mods = mods_parser::mods_from_str(&mods_str);
    let clock_rate = payload.clock_rate.unwrap_or(1.0);
    let lazer = payload.lazer.unwrap_or(true);

    let ar = payload.custom_ar.unwrap_or(0.0);
    let cs = payload.custom_cs.unwrap_or(0.0);
    let hp = payload.custom_hp.unwrap_or(0.0);
    let od = payload.custom_od.unwrap_or(0.0);

    // Calculate difficulty attributes
    let mut difficulty = rosu_pp::Difficulty::new()
    .lazer(lazer)
    .cs(cs, false)
    .ar(ar, false)
    .od(od, false)
    .hp(hp, false)
    .mods(mods);

    if clock_rate != 1.0 {
        difficulty = difficulty.clock_rate(clock_rate);
    }

    let diff_attrs = difficulty.calculate(&map);


    let stars = diff_attrs.stars();
    let max_combo = diff_attrs.max_combo();

    // Calculate performance attributes
    let mut performance = rosu_pp::Performance::new(diff_attrs.clone())
    .mods(mods)
    .lazer(lazer)
    .combo(payload.combo.unwrap_or(max_combo))
    .misses(payload.misses.unwrap_or(0))
    .accuracy(payload.accuracy.unwrap_or(100.0));

    if clock_rate != 1.0 {
        performance = performance.clock_rate(clock_rate);
    }

    let perf_attrs = performance.calculate();

    let pp = perf_attrs.pp();

    let mut perfect_performance = perf_attrs.clone().performance()
        .mods(mods)
        .lazer(lazer);

    if clock_rate != 1.0 {
        perfect_performance = perfect_performance.clock_rate(clock_rate);
    }

    let perfect_pp = perfect_performance.calculate().pp();

  
    let mut no_choke_performance = rosu_pp::Performance::new(diff_attrs)
        .lazer(lazer)
        .mods(mods)
        .n300(payload.n300.unwrap_or(0) + payload.misses.unwrap_or(0))
        .n100(payload.n100.unwrap_or(0))
        .n50(payload.n50.unwrap_or(0))
        .combo(max_combo)
        .misses(0);

    if let Some(acc) = payload.accuracy {
        no_choke_performance = no_choke_performance.accuracy(acc);
    }

    if clock_rate != 1.0 {
        no_choke_performance = no_choke_performance.clock_rate(clock_rate);
    }

    let no_choke_pp = no_choke_performance.calculate().pp();

    let perfect_combo = max_combo;
    let expected_bpm = map.bpm() as f64;

    Json(PpResponse {
        pp: pp,
        no_choke_pp: no_choke_pp, 
        perfect_pp: perfect_pp,

        star_rating: stars,
        perfect_combo: perfect_combo,
        expected_bpm: expected_bpm,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_calculate_choke_pp_direct() {
        let payload = PpRequest {
            map_path: "827803".to_string(),
            n300: Some(1200),
            n100: Some(10),
            n50: Some(2),
            misses: Some(7),
            combo:  Some(479),
            mods: Some("DT, RX".to_string()),
            accuracy: Some(98.50),
            lazer: Some(true),
            clock_rate: Some(1.5),
            custom_ar: Some(9.3),
            custom_cs: Some(4.0),
            custom_hp: Some(6.0),
            custom_od: Some(9.0),
        };

        let response = calculate_score_pp(axum::Json(payload)).await;
        
        assert!(response.0.pp >= 0.0);
        assert!(response.0.star_rating >= 0.0);

        let json_str = serde_json::to_string_pretty(&response.0).unwrap();
        println!("{}", json_str);
    }
}