use axum::{Json, extract::Json as AxumJson};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use crate::mods_parser;

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
}

#[derive(Serialize)]
pub struct PpResponse {
    pub pp: f64,
    pub no_choke_pp: f64,
    pub perfect_pp: f64,
    pub star_rating: f64,
}

pub async fn calculate_pp_handler(
    AxumJson(payload): AxumJson<PpRequest>
) -> Json<PpResponse> {
    let base_folder = r"E:\fa\nekoscience\bot\src\cache\beatmaps";

    let mut map_path = PathBuf::from(base_folder);
    map_path.push(format!("{}.osu", payload.map_path));
   
    let map = match rosu_pp::Beatmap::from_path(&map_path) {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Failed to load beatmap from {}: {:?}", map_path.display(), e);

            return Json(PpResponse {
                pp: 0.0,
                no_choke_pp: 0.0,
                star_rating: 0.0,
                perfect_pp: 0.0,
            });
        }
    };

    if let Err(e) = map.check_suspicion() {
        eprintln!("Beatmap suspicion check failed for {}: {:?}", map_path.display(), e);
        return Json(PpResponse {
            pp: 0.0,
            no_choke_pp: 0.0,
            star_rating: 0.0,
            perfect_pp: 0.0,
        });
    }


    let mods_str = payload.mods.unwrap_or("NM".to_string());
    let mods = mods_parser::mods_from_str(&mods_str);
    let clock_rate = payload.clock_rate.unwrap_or(1.0);
    let lazer = payload.lazer.unwrap_or(true);

    // Calculate difficulty attributes
    let mut difficulty = rosu_pp::Difficulty::new()
    .mods(mods)
    .lazer(lazer);

    if clock_rate != 1.0 {
        difficulty = difficulty.clock_rate(clock_rate);
    }

    let diff_attrs = difficulty.calculate(&map);


    let stars = diff_attrs.stars();
    let max_combo = diff_attrs.max_combo();

    // Calculate performance attributes
    let mut performance = rosu_pp::Performance::new(diff_attrs)
    
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
        .lazer(lazer);

    if clock_rate != 1.0 {
        perfect_performance = perfect_performance.clock_rate(clock_rate);
    }

    let perfect_pp = perfect_performance.calculate().pp();

  
    let mut no_choke_performance = perf_attrs.performance()
        .mods(mods)        
        .accuracy(payload.accuracy.unwrap_or(100.0))
        .lazer(lazer)
        .n300(payload.n300.unwrap_or(0) + payload.misses.unwrap_or(0))
        .n100(payload.n100.unwrap_or(0))
        .n50(payload.n50.unwrap_or(0))
        .misses(0);

    if clock_rate != 1.0 {
        no_choke_performance = no_choke_performance.clock_rate(clock_rate);
    }

    let no_choke_pp = no_choke_performance.calculate().pp();


    // println!("Lazer: {:?}", lazer);

    Json(PpResponse {
        pp: pp,
        no_choke_pp: no_choke_pp, 
        perfect_pp: perfect_pp,
        star_rating: stars,
    })
}
